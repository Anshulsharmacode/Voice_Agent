# Voice Agent

Local tool-calling voice/text agent powered by an Ollama chat model.

This project provides:

- `LLMService` wrapper for Ollama + LangChain chat/LLM clients
- Function-calling tool layer (`function_calling/`)
- Optional speech-to-text module using Whisper (`s2t/whisper.py`)
- Structured logging to console and `logs/agent.log`

## Highlights

- Async tool execution with OpenAI-style tool schemas
- Safe command execution guardrails (`execute_command`)
- File operation tools (`read`, `write`, `replace`, `insert`)
- Web utilities (`search`, `fetch page content`, `open browser`)
- Task planning helpers (`create_plan`, `track_task`, `task_is_done`)

## Project Structure

```text
VoiceAgent/
├── main.py                    # Example entry point
├── llm_service/
│   └── llm.py                 # LLMService (model + tool loop)
├── function_calling/
│   ├── __init__.py            # Tool registry + dispatcher
│   ├── calculator.py
│   ├── execute_command.py
│   ├── file_read.py
│   ├── write_to_file.py
│   ├── replace_in_file.py
│   ├── insert_in_file.py
│   ├── web_search.py
│   ├── webpage_content.py
│   ├── open_browser.py
│   ├── plan.py
│   ├── message.py
│   ├── finish_task.py
│   └── plan.md
├── s2t/
│   └── whisper.py             # Optional speech-to-text
└── logs/
    ├── logger.py
    └── agent.log
```

## Requirements

Core:

- Python 3.10+
- Ollama running locally (`http://localhost:11434`)
- An Ollama model pulled (example: `qwen3:0.6b`)

Python packages:

- `langchain-ollama` (or `langchain-community`)
- `langchain-core`
- `duckduckgo-search`
- `aiohttp`

Optional speech mode:

- `torch`
- `transformers`
- `numpy`
- Linux `arecord` command (`alsa-utils`)

## Setup

```bash
git clone <your-repo-url>
cd VoiceAgent
python -m venv .venv
source .venv/bin/activate
pip install langchain-ollama langchain-core duckduckgo-search aiohttp
```

If you use speech-to-text:

```bash
pip install torch transformers numpy
sudo apt-get install -y alsa-utils
```

Start Ollama and pull a model:

```bash
ollama serve
ollama pull qwen3:0.6b
```

## Run

```bash
python main.py
```

`main.py` currently sends a hardcoded prompt list to `LLMService.invoke_with_tools(...)`.

## How Tool Calling Works

1. User prompt is passed to `LLMService.invoke_with_tools`.
2. The model is bound to tool schemas from `function_calling.AVAILABLE_TOOLS`.
3. If the model emits tool calls, dispatcher runs `execute_tool(name, **args)`.
4. Tool output is returned back to the model as `ToolMessage`.
5. Loop continues until model returns final text or max iterations hit.

## Available Tools

| Tool Name             | Purpose                                |
| --------------------- | -------------------------------------- |
| `calculate`           | Evaluate math expressions safely       |
| `get_weather_info`    | Return mock weather response           |
| `search_web`          | DuckDuckGo text search                 |
| `get_webpage_content` | Fetch full HTML for a URL              |
| `open_browser`        | Open a URL/search in browser           |
| `execute_command`     | Run shell commands with safety filters |
| `read_file`           | Read file with line controls           |
| `write_file`          | Create/overwrite file                  |
| `replace_in_file`     | Replace exact content block            |
| `insert_in_file`      | Insert content at line number          |
| `create_plan`         | Create task checklist                  |
| `track_task`          | Show plan progress                     |
| `task_is_done`        | Mark task complete                     |
| `generic_response`    | Return plain message                   |
| `end_conversation`    | Signal completion                      |

## Notes About Safety

- `execute_command` blocks dangerous patterns (`sudo`, `rm`, destructive operations, etc.).
- File tools restrict operations to the active working directory unless explicitly set.
- Web tools return clear dependency errors if required packages are not installed.

## Common Issues

1. `ImportError: ChatOllama not available`

- Install: `pip install langchain-ollama`

2. `Error: Missing dependency duckduckgo-search`

- Install: `pip install duckduckgo-search`

3. `Error: Missing dependency aiohttp`

- Install: `pip install aiohttp`

4. Model not responding

- Verify Ollama is running and model exists:

```bash
curl http://localhost:11434/api/tags
```

## Quick Customization

In `main.py`, change model/config:

```python
llm = LLMService(
    model_name="qwen3:0.6b",
    base_url="http://localhost:11434",
    temperature=0.2,
    use_chat=True,
)
```

Limit tools for a request:

```python
answer = await llm.invoke_with_tools(
    "Summarize this page",
    tool_names=["get_webpage_content", "generic_response"],
)
```
