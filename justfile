set dotenv-load

export EDITOR := 'nvim'

alias c := check
alias e := example
alias f := fmt
alias r := run
alias t := test

default:
  just --list

all: fmt check readme

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
    --max-groupby-columns 5 \
    --max-merges 5 \
    --max-projection-columns 5 \
    --max-selection-conditions 10 \
    --num-queries 10000 \
    --output-file results/queries.txt \
    --schema example/schema.json \
    {{args}}

fmt:
  ruff check --select I --fix && ruff format

populate-results-directory *args:
  uv run pqg  \
    --max-groupby-columns 5 \
    --max-merges 5 \
    --max-projection-columns 5 \
    --max-selection-conditions 10 \
    --num-queries 10000 \
    --output-file results/single-line.txt \
    --schema example/schema.json

  uv run pqg  \
    --max-groupby-columns 5 \
    --max-merges 5 \
    --max-projection-columns 5 \
    --max-selection-conditions 10 \
    --multi-line \
    --num-queries 10000 \
    --output-file results/multi-line.txt \
    --schema example/schema.json

readme:
  present --in-place README.md

run *args:
  uv run pqg {{args}}

test *args:
  uv run pytest --verbose {{args}}
