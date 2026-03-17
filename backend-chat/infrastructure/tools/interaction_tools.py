from typing import Optional
from langchain.tools import tool


@tool
def think(thought: str) -> str:
    """
    Use esta ferramenta para raciocinar passo a passo ANTES de tomar qualquer decisão ou executar uma ação.

    QUANDO USAR:
    - Antes de chamar qualquer ferramenta de ação (criar work item, listar projetos, etc.)
    - Quando o pedido envolver múltiplas etapas (ex: criar Epic → User Stories → Tasks)
    - Para verificar se possui TODOS os parâmetros obrigatórios antes de agir
    - Para decidir qual ferramenta chamar a seguir

    EXEMPLO de uso antes de criar uma Epic:
    think("O usuário quer criar uma Epic. Tenho: título='X'. Falta: projeto. Devo listar os projetos e perguntar ao usuário qual usar antes de prosseguir.")

    A ferramenta não executa nenhuma ação — apenas registra o raciocínio e retorna o pensamento para o contexto.
    """
    print(f"[THOUGHT] {thought}")
    return thought


@tool
def ask_user(question: str, options: Optional[list[str]] = None) -> str:
    """
    Use esta ferramenta SEMPRE que uma informação obrigatória estiver ausente antes de executar qualquer ação.

    QUANDO USAR (obrigatório):
    - O usuário não especificou o projeto onde criar work items
    - Qualquer parâmetro obrigatório de outra ferramenta está faltando
    - Há ambiguidade que exige uma escolha do usuário

    NUNCA:
    - Selecione um projeto automaticamente a partir de uma listagem
    - Invente ou assuma valores não fornecidos pelo usuário

    Parâmetros:
    - question: A pergunta clara e objetiva a ser feita ao usuário
    - options: Lista de opções disponíveis para o usuário escolher (ex: nomes de projetos)

    A ferramenta sinaliza que o agente deve pausar e aguardar a resposta do usuário
    na próxima mensagem antes de executar qualquer ação.
    """
    if options:
        formatted = "\n".join(f"  {i + 1}. {opt}" for i, opt in enumerate(options))
        return f"AGUARDANDO_RESPOSTA: {question}\n\nOpções:\n{formatted}"
    return f"AGUARDANDO_RESPOSTA: {question}"
