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
    --allow-groupby \
    --max-merges 3 \
    --max-projection-columns 5 \
    --max-selection-conditions 4 \
    --num-queries 1000 \
    --output-file results/queries.txt \
    --schema example/schema.json \
    {{args}}

fmt:
  ruff check --select I --fix && ruff format

readme:
  present --in-place README.md

run *args:
  uv run pqg {{args}}

test:
  uv run pytest --verbose
