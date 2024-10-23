set dotenv-load

export EDITOR := 'nvim'

default:
  just --list

build:
  uv build

dev-deps:
  cargo install present

check:
  uv run ruff check

example:
  uv run pqg  \
    --num-queries 100 \
    --output-file results/queries.txt \
    --query-structure examples/query_parameters.json \
    --schema examples/data_structure_tpch_csv.json

fmt:
  ruff check --select I --fix && ruff format

readme:
  present --in-place README.md

run *args:
  uv run pqg {{args}}

test:
  uv run pytest --verbose
