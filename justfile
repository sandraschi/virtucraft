set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

test:
    uv run pytest

check:
    uv run ruff check .

fmt:
    uv run ruff format .

run-mcp:
    uv run virtucraft-cli mcp
