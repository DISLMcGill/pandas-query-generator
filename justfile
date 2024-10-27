set dotenv-load

export EDITOR := 'nvim'

alias c := check
alias f := fmt
alias r := run
alias t := test

default:
  just --list

all: fmt check readme

build:
  uv build

dev-deps:
  cargo install present tokei typos

check:
  uv run ruff check

count:
  tokei src

fmt:
  ruff check --select I --fix && ruff format

generate-example-output:
  ./bin/generate-example-output

publish:
  rm -rf dist && uv build && uv publish

readme:
  present --in-place README.md && typos --write-changes README.md

run *args:
  uv run pqg  \
    --max-groupby-columns 5 \
    --max-merges 5 \
    --max-projection-columns 10 \
    --max-selection-conditions 10 \
    --num-queries 10000 \
    --output-file queries.txt \
    --sort \
    {{args}}

test *args:
  uv run pytest --verbose {{args}}
