import asyncio
from typing import AsyncGenerator

# Attempt to import actual libraries used in the notebook; if unavailable, fall back to a simple implementation
try:
    from langchain_ollama import ChatOllama
    from langchain.tools import tool
    from langchain.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
    from typing_extensions import TypedDict, Annotated
    import operator
    from langgraph.graph import StateGraph, START, END
    LANG_AVAILABLE = True
except Exception:
    LANG_AVAILABLE = False


if LANG_AVAILABLE:
    # Initialize LLM (may require ollama running and model available)
    try:
        llm = ChatOllama(model="llama3.1:8b")
    except Exception:
        llm = None

    # Define tools
    @tool
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @tool
    def divide(a: int, b: int) -> float:
        """Divide two numbers."""
        return a / b

    tools = [add, multiply, divide]
    tools_by_name = {t.name: t for t in tools}

    model_with_tools = llm.bind_tools(tools) if llm is not None else None

    class MessagesState(TypedDict):
        messages: Annotated[list[AnyMessage], operator.add]
        llm_calls: int

    def llm_call(state: dict):
        return {
            "messages": [
                model_with_tools.invoke([
                    SystemMessage(content="You are an expert SAP BTP consultant with deep knowledge of cloud platforms and enterprise architecture. You can perform arithmetic calculations when needed using the provided tools.")
                ] + state["messages"])
            ],
            "llm_calls": state.get('llm_calls', 0) + 1,
        }

    def tool_node(state: dict):
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}

    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tool_node"
        return END

    agent_builder = StateGraph(MessagesState)
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", tool_node)
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    agent_builder.add_edge("tool_node", "llm_call")
    agent = agent_builder.compile()


async def stream_agent(question: str) -> AsyncGenerator[dict, None]:
    """Async generator that yields dicts describing intermediate steps and final answer.

    Yields items with shape {"type": "analysis|step|final|error", "text": str}
    """
    # If LLM/tools aren't available, fallback to dummy behavior
    if not LANG_AVAILABLE or llm is None or model_with_tools is None:
        if any(tok.isdigit() for tok in question):
            steps = [
                {"type": "analysis", "text": f"Parsing question: {question}"},
                {"type": "step", "text": "Extract numbers and operations"},
                {"type": "step", "text": "Compute intermediate result: 3 + 4 = 7"},
                {"type": "step", "text": "Compute final: 7 / 3 = 2.3333333333"},
                {"type": "final", "text": "2.3333333333"},
            ]
        else:
            steps = [
                {"type": "analysis", "text": f"Identified as SAP BTP question: {question}"},
                {"type": "step", "text": "Retrieve XSUAA definition from knowledge"},
                {"type": "final", "text": "XSUAA is SAP's authorization and authentication service on BTP..."},
            ]
        for s in steps:
            await asyncio.sleep(0.6)
            yield s
        return

    # If we have an LLM with tools, ask the LLM first and only run tools when requested
    try:
        from langchain.messages import SystemMessage, ToolMessage, HumanMessage

        # initial conversation state: system + user
        state_msgs = [
            SystemMessage(content="""You are a helpful AI assistant with expertise in SAP BTP, cloud platforms, and software development.

IMPORTANT: Answer questions directly using your knowledge. DO NOT use any tools unless the user explicitly asks you to perform a mathematical calculation.

You have access to these calculation tools ONLY for arithmetic:
- add(a, b): Add two numbers
- multiply(a, b): Multiply two numbers
- divide(a, b): Divide two numbers

Rules:
- If the question is about concepts, definitions, or explanations → Answer directly WITHOUT using any tools
- If the question asks to calculate, compute, or solve a math problem → Use the appropriate tools
- Never use tools for non-mathematical questions

Examples:
- "What is XSUAA?" → Answer directly, NO tools
- "Explain SAP BTP" → Answer directly, NO tools
- "Calculate 5 + 3" → Use add tool
- "What is 10 times 4?" → Use multiply tool"""),
            HumanMessage(content=question)
        ]

        while True:
            loop = asyncio.get_running_loop()
            # invoke the model that has tools bound
            resp = await loop.run_in_executor(None, lambda: model_with_tools.invoke(state_msgs))

            # If the model returned textual content, yield it as analysis
            content = getattr(resp, "content", None)
            if content:
                yield {"type": "analysis", "text": content}

            # Check for tool calls
            tool_calls = getattr(resp, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name")
                    args = tc.get("args", {})
                    tool = tools_by_name.get(name)
                    if tool is None:
                        obs = f"Unknown tool: {name}"
                    else:
                        try:
                            obs = await loop.run_in_executor(None, lambda: tool.invoke(args))
                        except Exception as e:
                            obs = f"Tool {name} failed: {e}"
                    # yield the tool observation
                    yield {"type": "step", "text": f"{name} -> {obs}"}
                    # append observation for next LLM call
                    state_msgs.append(ToolMessage(content=obs, tool_call_id=tc.get("id")))
                # continue loop to let LLM react to tool outputs
                continue

            # No tool calls: final answer
            final_text = content if content else str(resp)
            yield {"type": "final", "text": final_text}
            break
    except Exception as e:
        yield {"type": "error", "text": f"Agent invocation failed: {e}"}
