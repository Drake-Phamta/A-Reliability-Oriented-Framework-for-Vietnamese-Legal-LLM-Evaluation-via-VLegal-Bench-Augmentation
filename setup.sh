curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.13
source .venv/bin/activate
uv sync 
curl -fsSL https://ollama.com/install.sh | sh
ollama run gemma4:e4b-it-q8_0