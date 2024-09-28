set dotenv-load

export EDITOR := 'nvim'

default:
  just --list

build:
  uv build

check:
  uv run ruff check

example:
  rm -rf results/*
  uv run src --params examples/query_parameters.json --schema examples/data_structure_tpch_csv.json

fmt:
  ruff check --select I --fix
  ruff format

run *args:
  uv run src {{args}}
