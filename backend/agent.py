import asyncio
from typing import AsyncGenerator
import os
from pathlib import Path
import re

# Configuration for XSUAA repository scanning
XSUAA_REPO_PATH = os.getenv("XSUAA_REPO_PATH", "/Users/I567440/Desktop/Coding/SAP/xsuaa")
ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".vue", ".java", ".json", ".yaml", ".yml", ".md", ".txt", ".jsx", ".tsx"}
BLACKLIST_DIRS = {"node_modules", "dist", "build", "__pycache__", ".git", "target", "venv", ".env"}
BLACKLIST_FILES = {".env", ".key", ".pem", ".p12", ".jks"}
MAX_FILE_SIZE = 1024 * 1024  # 1MB

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

    @tool
    def search_xsuaa_files(keyword: str, file_pattern: str = "*") -> str:
        """Search for files in the XSUAA repository containing a specific keyword.

        Args:
            keyword: The keyword or pattern to search for in file contents (case-insensitive)
            file_pattern: Optional file name pattern (e.g., '*.py' for Python files, '*auth*' for files with 'auth' in name)

        Returns:
            A formatted string listing matching files with line numbers and context
        """
        try:
            if not os.path.exists(XSUAA_REPO_PATH):
                return f"Error: XSUAA repository not found at {XSUAA_REPO_PATH}"

            results = []
            keyword_lower = keyword.lower()

            for root, dirs, files in os.walk(XSUAA_REPO_PATH):
                # Skip blacklisted directories
                dirs[:] = [d for d in dirs if d not in BLACKLIST_DIRS]

                for file in files:
                    # Check file extension and blacklist
                    if Path(file).suffix not in ALLOWED_EXTENSIONS:
                        continue
                    if any(bl in file for bl in BLACKLIST_FILES):
                        continue

                    # Check file pattern match
                    if file_pattern != "*" and not Path(file).match(file_pattern):
                        continue

                    file_path = Path(root) / file

                    # Check file size
                    if file_path.stat().st_size > MAX_FILE_SIZE:
                        continue

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines, 1):
                                if keyword_lower in line.lower():
                                    rel_path = file_path.relative_to(XSUAA_REPO_PATH)
                                    results.append(f"{rel_path}:{i}: {line.strip()}")
                    except Exception:
                        continue

            if not results:
                return f"No files found containing '{keyword}' in the XSUAA repository."

            # Limit results to avoid overwhelming the LLM
            if len(results) > 50:
                results = results[:50]
                results.append(f"... (showing first 50 matches)")

            return "\n".join(results)
        except Exception as e:
            return f"Error searching files: {str(e)}"

    @tool
    def search_xsuaa_functions(function_name: str) -> str:
        """Search for function, method, or endpoint definitions in the XSUAA repository.

        This tool searches for function/method definitions, REST endpoints, and API routes.
        It looks for common patterns like:
        - Function definitions: def function_name, function function_name, functionName
        - Class methods: class methods with the name
        - REST endpoints: @app.route, @router, @RequestMapping, app.get/post/put/delete
        - Async functions: async def function_name

        Args:
            function_name: The name of the function, method, or endpoint to search for (e.g., 'updateIdentityProvider')

        Returns:
            Matching function definitions with file paths, line numbers, and context
        """
        try:
            if not os.path.exists(XSUAA_REPO_PATH):
                return f"Error: XSUAA repository not found at {XSUAA_REPO_PATH}"

            results = []

            # Build regex patterns for different programming languages
            patterns = [
                # Python: def function_name, async def function_name
                rf"(async\s+)?def\s+{re.escape(function_name)}\s*\(",
                # JavaScript/TypeScript: function functionName, const functionName =, functionName:
                rf"(async\s+)?function\s+{re.escape(function_name)}\s*\(",
                rf"(const|let|var)\s+{re.escape(function_name)}\s*=\s*(async\s+)?\(",
                rf"{re.escape(function_name)}\s*:\s*(async\s+)?\(",
                # Java: public/private/protected returnType functionName(
                rf"(public|private|protected)\s+\w+\s+{re.escape(function_name)}\s*\(",
                # REST endpoints with the function name in path or handler
                rf"@(app|router|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping).*{re.escape(function_name)}",
                rf"(app|router)\.(get|post|put|delete|patch)\([^)]*{re.escape(function_name)}",
                # Class definitions
                rf"class\s+{re.escape(function_name)}",
            ]

            for root, dirs, files in os.walk(XSUAA_REPO_PATH):
                dirs[:] = [d for d in dirs if d not in BLACKLIST_DIRS]

                for file in files:
                    if Path(file).suffix not in ALLOWED_EXTENSIONS:
                        continue
                    if any(bl in file for bl in BLACKLIST_FILES):
                        continue

                    file_path = Path(root) / file

                    if file_path.stat().st_size > MAX_FILE_SIZE:
                        continue

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()

                        for i, line in enumerate(lines, 1):
                            # Check if any pattern matches
                            for pattern in patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    rel_path = file_path.relative_to(XSUAA_REPO_PATH)
                                    # Include context: 2 lines before and 5 lines after
                                    context_start = max(0, i - 3)
                                    context_end = min(len(lines), i + 6)
                                    context_lines = []
                                    for j in range(context_start, context_end):
                                        marker = ">>>" if j == i - 1 else "   "
                                        context_lines.append(f"{marker} {j+1:4d} | {lines[j].rstrip()}")

                                    results.append(f"\n{rel_path}:{i}\n" + "\n".join(context_lines))
                                    break  # Don't match multiple patterns on same line
                    except Exception:
                        continue

            if not results:
                return f"No function or endpoint definitions found for '{function_name}' in the XSUAA repository.\nTip: Try searching with search_xsuaa_files('{function_name}') for broader results."

            # Limit results
            if len(results) > 20:
                results = results[:20]
                results.append(f"\n... (showing first 20 matches. Use read_xsuaa_file to see complete implementations)")

            return "\n".join(results)
        except Exception as e:
            return f"Error searching for functions: {str(e)}"

    @tool
    def read_xsuaa_file(file_path: str, start_line: int = 1, end_line: int = -1) -> str:
        """Read the content of a specific file in the XSUAA repository.

        Args:
            file_path: Relative path to the file within the XSUAA repository
            start_line: Starting line number (1-based, default: 1)
            end_line: Ending line number (1-based, default: -1 for entire file)

        Returns:
            The file content with line numbers
        """
        try:
            # Strip leading slash if present to ensure relative path
            file_path = file_path.lstrip('/')
            full_path = Path(XSUAA_REPO_PATH) / file_path

            if not full_path.exists():
                return f"Error: File not found at {file_path}"

            if not str(full_path).startswith(str(Path(XSUAA_REPO_PATH).resolve())):
                return "Error: Access denied - path outside XSUAA repository"

            if full_path.stat().st_size > MAX_FILE_SIZE:
                return f"Error: File too large (max {MAX_FILE_SIZE} bytes)"

            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            if end_line == -1:
                end_line = len(lines)

            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)

            result_lines = []
            for i, line in enumerate(lines[start_idx:end_idx], start=start_line):
                result_lines.append(f"{i:4d} | {line.rstrip()}")

            return "\n".join(result_lines)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @tool
    def list_xsuaa_structure(directory: str = ".", max_depth: int = 3) -> str:
        """List the directory structure of the XSUAA repository.

        Args:
            directory: Relative directory path within XSUAA repository (default: root)
            max_depth: Maximum depth to traverse (default: 3)

        Returns:
            A tree-like structure of directories and files
        """
        try:
            # Strip leading slash if present to ensure relative path
            directory = directory.lstrip('/')
            full_path = Path(XSUAA_REPO_PATH) / directory

            if not full_path.exists():
                return f"Error: Directory not found at {directory}"

            if not str(full_path).startswith(str(Path(XSUAA_REPO_PATH).resolve())):
                return "Error: Access denied - path outside XSUAA repository"

            def build_tree(path: Path, prefix: str = "", depth: int = 0) -> list:
                if depth > max_depth:
                    return []

                items = []
                try:
                    entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                    entries = [e for e in entries if e.name not in BLACKLIST_DIRS and not any(bl in e.name for bl in BLACKLIST_FILES)]

                    for i, entry in enumerate(entries):
                        is_last = i == len(entries) - 1
                        current_prefix = "└── " if is_last else "├── "
                        next_prefix = prefix + ("    " if is_last else "│   ")

                        if entry.is_dir():
                            items.append(f"{prefix}{current_prefix}{entry.name}/")
                            items.extend(build_tree(entry, next_prefix, depth + 1))
                        else:
                            if entry.suffix in ALLOWED_EXTENSIONS:
                                size = entry.stat().st_size
                                size_str = f"{size} bytes" if size < 1024 else f"{size//1024} KB"
                                items.append(f"{prefix}{current_prefix}{entry.name} ({size_str})")
                except PermissionError:
                    pass

                return items

            tree = [f"{directory}/ (XSUAA Repository)"]
            tree.extend(build_tree(full_path))

            return "\n".join(tree)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    tools = [add, multiply, divide, search_xsuaa_files, search_xsuaa_functions, read_xsuaa_file, list_xsuaa_structure]
    tools_by_name = {t.name: t for t in tools}

    # Add normalized names (without underscores) to handle LLM tool name formatting
    for tool in tools:
        normalized_name = tool.name.replace("_", "")
        if normalized_name != tool.name:
            tools_by_name[normalized_name] = tool

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

You have access to these tools:

Calculation tools (use ONLY for explicit math requests):
- add(a, b): Add two numbers
- multiply(a, b): Multiply two numbers
- divide(a, b): Divide two numbers

Code scanning tools (use for XSUAA code questions):
- search_xsuaa_functions(function_name): Search for function/method/endpoint definitions (BEST for finding specific functions or endpoints)
- search_xsuaa_files(keyword, file_pattern): Search for code containing a keyword (BEST for concepts, variables, or general searches)
- read_xsuaa_file(file_path, start_line, end_line): Read specific file content with line numbers
- list_xsuaa_structure(directory, max_depth): Show directory structure of XSUAA repository

Rules:
1. For general knowledge questions → Answer directly WITHOUT tools
2. For math calculations → Use calculation tools
3. For XSUAA code-specific questions → Choose the right tool:

   FOR FINDING ENDPOINTS/FUNCTIONS (e.g., "updateIdentityProvider endpoint", "login function"):
   a) Use search_xsuaa_functions(function_name) FIRST - it finds function definitions with context
   b) Then use read_xsuaa_file to see the complete implementation
   c) Include file paths, line numbers, and explain the code flow

   FOR FINDING CONCEPTS/PATTERNS (e.g., "authentication logic", "JWT validation"):
   a) Use search_xsuaa_files(keyword) to find all occurrences
   b) Then use read_xsuaa_file to examine specific code
   c) Reference the actual code in your answer

Examples of user questions and how to handle them:

General Knowledge (NO TOOLS):
- "What is XSUAA?"
- "Explain microservices architecture"
- "What are SAP BTP services?"

Math Calculations (USE CALCULATION TOOLS):
- "Calculate 5 + 3" → Use add(5, 3)
- "What is 156 multiplied by 89?" → Use multiply(156, 89)

Finding Specific Functions/Endpoints (USE search_xsuaa_functions):
- "Explain how the updateIdentityProvider endpoint works" → search_xsuaa_functions("updateIdentityProvider"), then read_xsuaa_file
- "Show me the login function implementation" → search_xsuaa_functions("login"), then read_xsuaa_file
- "Where is the token refresh function defined?" → search_xsuaa_functions("refresh") or search_xsuaa_functions("refreshToken")
- "Find the validateToken method" → search_xsuaa_functions("validateToken")
- "How does the authentication middleware work?" → search_xsuaa_functions("middleware") or search_xsuaa_functions("authenticate")

Finding Concepts/Patterns (USE search_xsuaa_files):
- "How is authentication implemented in XSUAA?" → search_xsuaa_files("authentication")
- "Show me JWT validation code" → search_xsuaa_files("jwt")
- "Find error handling patterns" → search_xsuaa_files("error") or search_xsuaa_files("exception")
- "How does session management work?" → search_xsuaa_files("session")
- "Show me OAuth2 flow implementation" → search_xsuaa_files("oauth2")

Exploring Code Structure (USE list_xsuaa_structure):
- "What files are in the XSUAA repository?" → list_xsuaa_structure()
- "Show me the structure of the auth module" → list_xsuaa_structure("auth")
- "List files in the src directory" → list_xsuaa_structure("src")

IMPORTANT: When providing your final answer:
- DO NOT mention which tools you used (e.g., don't say "I searched using search_xsuaa_functions" or "I used read_xsuaa_file")
- DO NOT explain your approach or reasoning process (e.g., don't say "To answer this question, I'll use..." or "I will call...")
- Just use the tools silently and then provide the answer directly
- Focus on explaining the actual code, its functionality, and how it works
- Cite file paths and line numbers naturally (e.g., "In authentication.py at line 45...")
- Present information as if you have direct knowledge of the codebase
- NEVER output JSON tool calls or parameters in your response"""),
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

                    # Show user-friendly message about what tool is being executed
                    if name in ["search_xsuaa_files", "searchxsuaafiles"]:
                        keyword = args.get("keyword", "")
                        pattern = args.get("file_pattern", "*")
                        if pattern and pattern != "*":
                            yield {"type": "step", "text": f"🔍 Searching XSUAA repository for '{keyword}' in {pattern} files..."}
                        else:
                            yield {"type": "step", "text": f"🔍 Searching XSUAA repository for '{keyword}'..."}
                    elif name in ["search_xsuaa_functions", "searchxsuaafunctions"]:
                        function_name = args.get("function_name", "")
                        yield {"type": "step", "text": f"🔎 Searching for function/endpoint definition: {function_name}..."}
                    elif name in ["read_xsuaa_file", "readxsuaafile"]:
                        file_path = args.get("file_path", "")
                        start_line = args.get("start_line", 1)
                        end_line = args.get("end_line", -1)
                        if end_line == -1:
                            yield {"type": "step", "text": f"📖 Reading file: {file_path} (from line {start_line})"}
                        else:
                            yield {"type": "step", "text": f"📖 Reading file: {file_path} (lines {start_line}-{end_line})"}
                    elif name in ["list_xsuaa_structure", "listxsuaastructure"]:
                        directory = args.get("directory", ".")
                        yield {"type": "step", "text": f"📂 Listing XSUAA directory structure: {directory}"}
                    elif name in ["add", "multiply", "divide"]:
                        # Show calculation steps
                        a = args.get("a", 0)
                        b = args.get("b", 0)
                        op_symbols = {"add": "+", "multiply": "×", "divide": "÷"}
                        symbol = op_symbols.get(name, name)
                        yield {"type": "step", "text": f"🧮 Computing: {a} {symbol} {b}"}
                    else:
                        # Generic tool execution message
                        yield {"type": "step", "text": f"⚙️ Executing: {name}"}

                    tool = tools_by_name.get(name)
                    if tool is None:
                        obs = f"Unknown tool: {name}"
                    else:
                        try:
                            # Fix closure issue by creating a proper closure with default argument
                            def call_tool(t=tool, a=args):
                                return t.invoke(a)
                            obs = await loop.run_in_executor(None, call_tool)
                        except Exception as e:
                            obs = f"Tool {name} failed: {e}"

                    # Detect if this is a file reading operation and emit code_snippet event
                    if name in ["read_xsuaa_file", "readxsuaafile"] and not obs.startswith("Error:"):
                        file_path = args.get("file_path", "")
                        # Detect language from file extension
                        ext_to_lang = {
                            ".py": "python", ".js": "javascript", ".ts": "typescript",
                            ".vue": "vue", ".java": "java", ".json": "json",
                            ".yaml": "yaml", ".yml": "yaml", ".md": "markdown",
                            ".tsx": "typescript", ".jsx": "javascript"
                        }
                        file_extension = Path(file_path).suffix
                        language = ext_to_lang.get(file_extension, "plaintext")

                        print(f"DEBUG: file_path={file_path}, extension={file_extension}, language={language}", flush=True)

                        # Extract line numbers from args
                        start = args.get("start_line", 1)
                        end = args.get("end_line", -1)
                        line_range = f"{start}-{end}" if end != -1 else f"{start}+"

                        yield {
                            "type": "code_snippet",
                            "file": file_path,
                            "lines": line_range,
                            "code": obs,
                            "language": language
                        }
                        # Don't show raw output for file reads since we're showing code snippet
                    elif name in ["search_xsuaa_files", "searchxsuaafiles"]:
                        # Show search results in a more compact format
                        result_lines = obs.split('\n')
                        file_count = len([l for l in result_lines if l.strip() and ':' in l and not l.startswith('...')])
                        if file_count > 0:
                            yield {"type": "step", "text": f"✅ Found {file_count} matches in the codebase"}
                        else:
                            yield {"type": "step", "text": "ℹ️ No matches found"}
                    elif name in ["search_xsuaa_functions", "searchxsuaafunctions"]:
                        # Show function search results summary and emit file references
                        result_lines = obs.split('\n')
                        match_count = len([l for l in result_lines if '>>>' in l])
                        if match_count > 0:
                            yield {"type": "step", "text": f"✅ Found {match_count} function definition(s)"}
                            # Extract and emit file references
                            for line in result_lines:
                                if line.strip() and ':' in line and not line.startswith(' '):
                                    parts = line.split(':')
                                    if len(parts) >= 2:
                                        file_ref = parts[0].strip()
                                        line_num = parts[1].strip()
                                        if file_ref and line_num.isdigit():
                                            yield {
                                                "type": "file_reference",
                                                "file": file_ref,
                                                "line": int(line_num)
                                            }
                        else:
                            yield {"type": "step", "text": "ℹ️ No function definitions found"}
                    elif name in ["list_xsuaa_structure", "listxsuaastructure"]:
                        # Show structure results summary and emit directory tree
                        result_lines = obs.split('\n')
                        yield {"type": "step", "text": f"✅ Listed {len(result_lines)} items"}
                        # Emit the tree structure for visual display
                        yield {
                            "type": "directory_tree",
                            "tree": obs
                        }
                    elif name in ["add", "multiply", "divide"]:
                        # Show calculation result
                        yield {"type": "step", "text": f"✅ Result: {obs}"}
                    else:
                        # yield regular tool observation for other tools (but not the raw output)
                        if not obs.startswith("Error:"):
                            yield {"type": "step", "text": f"✅ Completed"}

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
