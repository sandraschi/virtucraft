# VirtuCraft

VirtuCraft is a craft-pattern headless virtual machine and hypervisor workstation.

## Verbs
- `virtucraft vm list [--json]`
- `virtucraft vm info --vm NAME [--json]`
- `virtucraft snapshot list --vm NAME [--json]`
- `virtucraft snapshot create --vm NAME --snap NAME [--json]`
- `virtucraft snapshot delete --vm NAME --snap NAME [--json]`
- `virtucraft network list [--json]`
- `virtucraft host info [--json]`
- `virtucraft sandbox run --code "print('hi')"`
- `virtucraft tools`
- `virtucraft mcp`

## Lineage — the Storytold craft-app pattern

Storytold ArtCraft ([storytold/artcraft](https://github.com/storytold/artcraft) — "the IDE for artists") was the starting point. The 16 craft apps in the Storytold stable each ship one binary that is both the human CLI and the agent MCP server (stdio), headless-first, with `run.json` + report artifacts. That modus operandi and harness is what this repo implements; the code here is independent, the pattern is shared.
