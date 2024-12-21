set dotenv-load

export EDITOR := 'nvim'

alias c := check
alias f := fmt
alias r := run
alias t := test

default:
  just --list

all: fmt check readme

[group: 'app']
build:
  uv build

[group: 'release']
deploy-web: generate-docs
  cd www && bun run build && bunx gh-pages -d dist

[group: 'app']
dev-deps:
  cargo install present tokei typos

[group: 'check']
check:
  uv run ruff check

[group: 'check']
count:
  tokei src

[group: 'format']
fmt:
  ruff check --select I --fix && ruff format

[group: 'format']
fmt-web:
  cd www && prettier --write .

[group: 'generate']
generate-docs:
  cd docs && uv run sphinx-build -M html config build
  rm -rf www/public/docs
  uv run ./bin/flatten-docs.py --source docs/build/html --output www/public/docs
  just fmt-web

[group: 'generate']
generate-example-output:
  ./bin/generate-example-output

[group: 'release']
publish:
  rm -rf dist && uv build && uv publish

[group: 'format']
readme:
  present --in-place README.md && typos --write-changes README.md

[group: 'app']
run *args:
  uv run pqg {{args}}

[group: 'app']
serve-docs: generate-docs
  python3 -m http.server 8000 --directory docs/build/html

[group: 'app']
serve-web:
  cd www && bun install && bunx --bun vite

[group: 'test']
test *args:
  uv run pytest --verbose {{args}}
