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

deploy-web:
  cd www && bun run build && bunx gh-pages -d dist

dev-deps:
  cargo install present tokei typos

check:
  uv run ruff check

count:
  tokei src

fmt:
  ruff check --select I --fix && ruff format

fmt-web:
  cd www && prettier --write .

generate-docs:
  cd docs && uv run sphinx-build -M html config build
  rm -rf www/public/docs
  uv run ./bin/convert-docs.py --source docs/build/html --output www/public/docs

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
