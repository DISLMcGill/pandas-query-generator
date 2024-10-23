set dotenv-load

export EDITOR := 'nvim'

alias e := example
alias f := fmt
alias r := run
alias t := test

default:
  just --list

build:
  uv build

dev-deps:
  cargo install present tokei

check:
  uv run ruff check

count:
  tokei

example *args:
  uv run pqg  \
    --num-queries 1000 \
    --output-file results/queries.txt \
    --query-structure examples/query_structure.json \
    --schema examples/data_structure_tpch_csv.json \
    {{args}}

fmt:
  ruff check --select I --fix && ruff format

readme:
  present --in-place README.md

run *args:
  uv run pqg {{args}}

test:
  uv run pytest --verbose
