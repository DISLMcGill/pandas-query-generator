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

demo:
  just run \
    --groupby-aggregation-probability 0.5 \
    --max-groupby-columns 5 \
    --max-merges 10 \
    --max-projection-columns 10 \
    --max-selection-conditions 10 \
    --num-queries 1000 \
    --projection-probability 0.5 \
    --schema examples/tpch/schema.json \
    --selection-probability 0.5 \
    --sort \
    --verbose

deploy:
  cd www && bun run build && bunx gh-pages -d dist

dev-deps:
  cargo install present tokei typos

check:
  uv run ruff check

count:
  tokei src

fmt:
  ruff check --select I --fix && ruff format

generate-docs:
  cd docs && just build

generate-example-output:
  ./bin/generate-example-output

publish:
  rm -rf dist && uv build && uv publish

readme:
  present --in-place README.md && typos --write-changes README.md

run *args:
  uv run pqg {{args}}

serve-docs: generate-docs
  python3 -m http.server 8000 --directory docs/build/html

serve-web:
  cd www && bun install && bunx --bun vite

test *args:
  uv run pytest --verbose {{args}}
