set dotenv-load

export EDITOR := 'nvim'

default:
  just --list

build:
  uv build

check:
  uv run ruff check

format:
  uv run ruff format

run *args:
  uv run src {{args}}
