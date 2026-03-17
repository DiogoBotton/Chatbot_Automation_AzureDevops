from typing import List, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessageChunk, ToolMessage, SystemMessage
from langchain.agents import create_agent
from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from infrastructure.constants.prompts import get_system_prompt
from infrastructure.services.mcp_manager import MCPManager


class ChatbotService:
    """
    Orquestra o agente ReAct com streaming real de tokens.

    Fluxo em duas fases:
    1. Streaming: emite tokens de texto em tempo real + coleta chunks brutos
    2. Persistência: reconstrói mensagens completas e popula new_messages
    """

    _agent = None

    @classmethod
    def _get_agent(cls):
        """Cria o agente na primeira chamada e reutiliza nas seguintes."""
        if cls._agent is None:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=2)
            cls._agent = create_agent(llm, tools=MCPManager.get_tools())
        return cls._agent

    def _build_messages(
        self,
        user_query: str,
        chat_history: List[BaseMessage],
        project_id: str | None,
        project_name: str | None,
    ) -> List[BaseMessage]:
        """Monta a lista de mensagens com SystemMessage dinâmico baseado no projeto ativo."""
        sys_prompt = get_system_prompt(project_id=project_id, project_name=project_name)
        return [SystemMessage(content=sys_prompt)] + chat_history + [HumanMessage(content=user_query)]

    def _collect_messages(self, raw_chunks: list, new_messages: List[ConversationHistory]) -> None:
        """
        Reconstrói mensagens completas a partir dos chunks brutos do agente
        e popula new_messages na ordem correta para persistência no banco.

        Chamado APÓS o streaming terminar — separação clara entre stream e persistência.
        """
        current_ai: AIMessageChunk | None = None

        for chunk in raw_chunks:
            if isinstance(chunk, AIMessageChunk):
                # Novo AIMessage (nova chamada LLM) → salva o anterior
                if current_ai is not None and chunk.id != current_ai.id:
                    self._persist_ai(current_ai, new_messages)
                    current_ai = chunk
                elif current_ai is None:
                    current_ai = chunk
                else:
                    current_ai = current_ai + chunk

            elif isinstance(chunk, ToolMessage):
                # ToolMessage chega completo — salva o AIMessage pendente primeiro
                if current_ai is not None:
                    self._persist_ai(current_ai, new_messages)
                    current_ai = None

                new_messages.append(ConversationHistory(
                    role=MessageType.TOOL,
                    content=str(chunk.content),
                    tool_call_id=chunk.tool_call_id,
                ))

        # Salva o último AIMessage (resposta final do agente)
        if current_ai is not None:
            self._persist_ai(current_ai, new_messages)

    def _persist_ai(self, msg: AIMessageChunk, new_messages: List[ConversationHistory]) -> None:
        """Converte um AIMessageChunk acumulado em ConversationHistory."""
        if msg.tool_calls:
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                tool_calls=msg.tool_calls,
            ))
        elif msg.content:
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=msg.content,
            ))

    async def get_response_stream(
        self,
        user_query: str,
        chat_history: List[BaseMessage],
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> tuple[AsyncGenerator[str, None], List[ConversationHistory]]:
        """
        Executa o agente ReAct com streaming real de tokens.

        Fase 1 (streaming): itera os chunks do agente, emite tokens de texto
        em tempo real e coleta todos os chunks brutos numa lista.

        Fase 2 (persistência): após o stream completar, reconstrói as mensagens
        completas (AIMessage com tool_calls, ToolMessage, resposta final) e
        popula new_messages para o commit no banco.
        """
        new_messages: List[ConversationHistory] = []
        input_messages = self._build_messages(user_query, chat_history, project_id, project_name)
        agent = self._get_agent()

        async def _stream() -> AsyncGenerator[str, None]:
            raw_chunks: list = []

            async for chunk, metadata in agent.astream(
                {"messages": input_messages},
                config={"recursion_limit": 80},
                stream_mode="messages",
            ):
                if not metadata.get("langgraph_node"):
                    continue

                raw_chunks.append(chunk)

                # Streaming real: emite apenas tokens de texto (não tool calls)
                if isinstance(chunk, AIMessageChunk) and chunk.content and not chunk.tool_call_chunks:
                    yield chunk.content

            # Após o stream terminar: reconstrói e salva todas as mensagens
            self._collect_messages(raw_chunks, new_messages)

        return _stream(), new_messages
