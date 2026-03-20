from typing import List
from uuid import UUID
from fastapi import Depends, HTTPException
import logging
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from domains.conversation import Conversation
from domains.conversation_history import ConversationHistory
from domains.enums.message_type import MessageType
from infrastructure.services.chatbot_service import ChatbotService
from infrastructure.dtos.results.chat.message_history import MessageHistory
from infrastructure.dtos.results.chat.message_result import MessageResult
from data.database import get_db
from pydantic import BaseModel
from . import BaseHandler

# Request
class Command(BaseModel):
    input: str
    conversation_id: UUID
    project_id: str | None = None
    project_name: str | None = None

# Handle
class Chatbot(BaseHandler[Command, MessageResult]):
    def __init__(self, db: Session = Depends(get_db), chatbotService: ChatbotService = Depends()):
        self.db = db
        self.chatbotService = chatbotService

    async def execute(self, request: Command):
        conversation = (self.db
                        .query(Conversation)
                        .filter(Conversation.id == request.conversation_id)
                        .first()) if request.conversation_id else None
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
            
        history = []
        conversation_history: List[ConversationHistory] = (
                                    self.db.query(ConversationHistory)
                                    .filter(ConversationHistory.conversation_id == conversation.id)
                                    .order_by(ConversationHistory.id.asc())
                                    .all()
                                ) if conversation.id else []
        
        for ch in conversation_history:
            if ch.role == MessageType.ASSISTANT:
                history.append(AIMessage(ch.content, tool_calls=ch.tool_calls or []))
            elif ch.role == MessageType.USER:
                history.append(HumanMessage(ch.content))
            elif ch.role == MessageType.TOOL:
                history.append(ToolMessage(ch.content, tool_call_id=ch.tool_call_id))
        
        generator, new_messages = await self.chatbotService.get_response_stream(
            request.input, history, request.project_id, request.project_name
        )
        
        async def wrapped_generator():
            try:
                async for chunk in generator:
                    yield chunk
            except Exception as e:
                logging.error("Erro no stream", exc_info=e)
                yield "\n[Erro ao processar resposta]"
                return  # Não commita em caso de erro
            
            # Salva as novas mensagens no banco
            conversation.conversation_histories.append(ConversationHistory(role=MessageType.USER, content=request.input))
            conversation.conversation_histories.extend(new_messages)
            self.db.commit()

        return StreamingResponse(wrapped_generator(), media_type="text/plain")