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

## Status — does today / next week / non-goals

**Does today:** Python FastMCP, richest module split of the six
(cli/hypervisor/models/sandbox); 5 test fns; Wave-1 pilot per rebuild PLAN.

**Next week:** hypervisor-presence gate + skip-with-receipt; 3 recipes
(list-and-info, snapshot-roundtrip, network-create-delete); `serve` spec
decision.

**Non-goals:** sandbox executes untrusted code only with a confinement
story; long-lived sessions need `serve`, still undecided.

## Lineage — the Storytold craft-app pattern

Storytold ArtCraft ([storytold/artcraft](https://github.com/storytold/artcraft) — "the IDE for artists") was the starting point. The 16 craft apps in the Storytold stable each ship one binary that is both the human CLI and the agent MCP server (stdio), headless-first, with `run.json` + report artifacts. That modus operandi and harness is what this repo implements; the code here is independent, the pattern is shared.
