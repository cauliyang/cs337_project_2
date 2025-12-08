# Recipe Bot

Developed by group 4 in CS337, Fall 2025.

## Members

- [Logan Mappes]()
- [Katie Shao]()
- [Yangyang Li](yangyang.li@northwestern.edu)

## How to use

```sh
# clone the repo
git clone https://github.com/cauliyang/cs337_project_1.git

# install uv
pip install uv

# install dependencies
uv sync

```

## Run the bot

```sh
source .venv/bin/activate

cd rasa

# run the action server
rasa run actions

# run the shell and talk with the bot
rasa shell
```

### Debugging the bot

```sh
# Visualize stories
rasa visualize
```

## [Run the web UI](./rasa/UI.md)

```sh
cd rasa

# run the action server
rasa run actions

# run the rasa server
rasa run --enable-api --cors "*"

# open the web UI or build http server with `python -m http.server`
python -m http.server
open index.html
```

### Caveats

In macOS with M chip, we need to install NumPy 1.26.4 manually before running the bot.

```sh
uv sync

# fix api mismatch error
uv pip install --no-binary=numpy "numpy==1.26.4"

# source the venv
source .venv/bin/activate

# cd to rasa
cd rasa

# run the action server
rasa run actions

# run the shell and talk with the bot
rasa shell
```

## LLM Only

```sh
# install dependencies
uv sync --extra llm

# run the Agent
uv run recipebot-llm
```

## Hybrid

```sh
# install dependencies
uv sync --extra llm

# run the Agent
uv run recipebot-hybrid
```

## Development

```sh
# run the tests
uv run pytest -vls
# or
make test

# add Dependency
uv add requests

# run the linter before pushing
make lint
```
