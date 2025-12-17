from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import json
import os
import importlib
import types
from typing import AsyncGenerator, Callable, Any

app = FastAPI()

# Serve frontend static files from an available directory (prefer production build)
_static_dir = None
for candidate in ("./frontend", "./frontend-vue/dist", "./frontend-vue"):
    if os.path.isdir(os.path.abspath(candidate)):
        _static_dir = os.path.abspath(candidate)
        break

if _static_dir:
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")
else:
    # No static frontend available; skip mounting to avoid startup errors
    print("No frontend static directory found; continuing without static mount")


class Query(BaseModel):
    question: str


async def _dummy_agent(question: str) -> AsyncGenerator[dict, None]:
    """Fallback agent that yields example intermediate steps."""
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


def _import_agent_callable(path: str) -> Callable[..., Any]:
    """Import a callable using dotted path 'module:callable' or 'module.callable'.

    Returns the imported object or raises ImportError/AttributeError.
    """
    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        parts = path.rsplit(".", 1)
        module_path, attr = parts[0], parts[1]
    else:
        raise ImportError("Invalid AGENT_CALLABLE format")

    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _ensure_async_generator(obj: Any) -> Callable[[str], AsyncGenerator[dict, None]]:
    """Wrap different callable types into an async generator interface.

    Supported input types:
    - async generator function: used as-is
    - async function returning iterable/list: will iterate and yield
    - sync function returning iterable/list: will run in thread and yield
    """
    import inspect

    # Check if it's an async generator function
    if inspect.isasyncgenfunction(obj):
        # Return as-is, it already returns an async generator
        return obj

    # Check if it's an async function (coroutine function)
    if asyncio.iscoroutinefunction(obj):
        async def runner(question: str):
            res = await obj(question)
            # Check if result is an async generator
            if hasattr(res, "__aiter__"):
                async for item in res:
                    yield item
            # Otherwise treat as iterable
            else:
                for it in res:
                    yield it
        return runner

    # sync callable
    def is_sync_callable(f):
        return callable(f) and not asyncio.iscoroutinefunction(f) and not inspect.isasyncgenfunction(f)

    if is_sync_callable(obj):
        async def runner(question: str):
            loop = asyncio.get_running_loop()
            items = await loop.run_in_executor(None, lambda: obj(question))
            # If items is an async generator, iterate async
            if hasattr(items, "__aiter__"):
                async for it in items:
                    yield it
            else:
                for it in items:
                    yield it

        return runner

    raise TypeError("Unsupported agent callable type")


# Try to import user-provided agent callable from env var AGENT_CALLABLE
AGENT_CALLABLE = os.environ.get("AGENT_CALLABLE")
_agent_runner = None
if AGENT_CALLABLE:
    try:
        obj = _import_agent_callable(AGENT_CALLABLE)
        _agent_runner = _ensure_async_generator(obj)
        print(f"✓ Loaded agent from: {AGENT_CALLABLE}", flush=True)
    except Exception as e:
        print(f"✗ Failed importing AGENT_CALLABLE={AGENT_CALLABLE}: {e}", flush=True)
        _agent_runner = None

# If no AGENT_CALLABLE provided, try loading a notebook agent via AGENT_NOTEBOOK
if _agent_runner is None:
    AGENT_NOTEBOOK = os.environ.get("AGENT_NOTEBOOK")
    AGENT_VAR = os.environ.get("AGENT_VAR", "agent")
    if AGENT_NOTEBOOK:
        try:
            nb_path = os.path.abspath(AGENT_NOTEBOOK)
            with open(nb_path, "r", encoding="utf-8") as fh:
                nb = json.load(fh)

            # Collect code cells and concatenate their source into one string
            code_list = []
            for cell in nb.get("cells", []):
                if cell.get("cell_type") != "code":
                    continue
                src = cell.get("source", "")
                if isinstance(src, list):
                    src = "".join(src)
                code_list.append(src)
            code_cells = "\n\n".join(code_list)

            # Execute the concatenated code in a new globals dict
            agent_ns = {"__name__": "__agent_notebook__"}
            exec(code_cells, agent_ns)

            if AGENT_VAR in agent_ns:
                agent_obj = agent_ns[AGENT_VAR]
                _agent_runner = _ensure_async_generator(agent_obj)
                print(f"Loaded agent from notebook: {AGENT_NOTEBOOK}, var: {AGENT_VAR}")
            else:
                print(f"Notebook loaded but variable '{AGENT_VAR}' not found in {AGENT_NOTEBOOK}")
        except Exception as e:
            print(f"Failed loading notebook AGENT_NOTEBOOK={AGENT_NOTEBOOK}: {e}")
            _agent_runner = None


async def run_agent_stream(question: str):
    """Dispatch to the configured agent runner or fallback dummy."""
    if _agent_runner is not None:
        async for item in _agent_runner(question):
            yield item
        return

    async for item in _dummy_agent(question):
        yield item



@app.post("/api/ask")
async def ask(query: Query):
    async def event_generator():
        # Stream JSON lines (newline-delimited JSON)
        async for item in run_agent_stream(query.question):
            yield json.dumps(item) + "\n"

    return StreamingResponse(event_generator(), media_type="application/json")


@app.get("/")
async def index():
    # Serve the legacy static UI if present
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(index_path):
        html = open(index_path, "r").read()
        return HTMLResponse(content=html)
    return HTMLResponse(content="Agent backend running")
