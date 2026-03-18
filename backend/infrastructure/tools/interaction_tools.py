from typing import Optional
from langchain.tools import tool


@tool
def think(thought: str) -> str:
    """
    Ferramenta de raciocínio interno. Use para planejar etapas, verificar parâmetros e decidir a próxima ação antes de executar ferramentas. Não executa nenhuma ação externa.
    """
    print(f"[THOUGHT] {thought}")
    return thought


@tool
def ask_user(question: str, options: Optional[list[str]] = None) -> str:
    """
    Use para solicitar informações ao usuário quando um parâmetro obrigatório estiver ausente ou houver ambiguidade.
    Nunca assuma ou invente valores — sempre aguarde a resposta do usuário antes de prosseguir.
    """
    print(f"[ASK_USER] {question} {'Opções: ' + ', '.join(options) if options else ''}")
    if options:
        formatted = "\n".join(f"  {i + 1}. {opt}" for i, opt in enumerate(options))
        return f"AGUARDANDO_RESPOSTA: {question}\n\nOpções:\n{formatted}"
    return f"AGUARDANDO_RESPOSTA: {question}"


@tool
def finish_task(summary: str) -> str:
    """
    Chame esta ferramenta OBRIGATORIAMENTE como última ação após concluir todas as criações solicitadas.
    Passe um resumo do que foi criado. Não chame nenhuma outra ferramenta após esta.
    """
    print(f"[FINISH_TASK] {summary}")
    return f"CONCLUÍDO: {summary}"
