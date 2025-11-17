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

## Problem Cases to Fix

recipe url: https://www.allrecipes.com/recipe/20096/cheesy-ham-and-hash-brown-casserole/
wrong hour parsing in step 7:

```
Bake in the preheated oven until bubbly and lightly brown, about 1 hour.
⏱️  Time: 1 minutes
🔧 Tools: oven
```

## Project Description

- Free software: MIT License

## Credits
