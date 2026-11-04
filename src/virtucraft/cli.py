"""CLI entrypoint for VirtuCraft conforming to Craft Fleet specification."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import __version__
from .hypervisor import (
    create_snapshot,
    delete_snapshot,
    get_host_info,
    get_vm_info,
    list_networks,
    list_snapshots,
    list_vms,
)
from .sandbox import run_code_in_sandbox


def print_out(data: Any, as_json: bool = False) -> None:
    """Output either compact JSON or human-readable format."""
    if as_json:
        if hasattr(data, "model_dump"):
            print(json.dumps(data.model_dump()))
        elif isinstance(data, list):
            items = [item.model_dump() if hasattr(item, "model_dump") else item for item in data]
            print(json.dumps(items))
        else:
            print(json.dumps(data))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        elif hasattr(data, "model_dump"):
            for k, v in data.model_dump().items():
                print(f"{k}: {v}")
        elif isinstance(data, list):
            for item in data:
                print(item)
        else:
            print(data)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="virtucraft-cli",
        description="VirtuCraft: Headless virtual machine and hypervisor control craft",
    )
    parser.add_argument("--version", action="version", version=f"virtucraft {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # vm
    vm_parser = subparsers.add_parser("vm", help="Virtual machine lifecycle operations")
    vm_sub = vm_parser.add_subparsers(dest="vm_action")

    vm_list = vm_sub.add_parser("list", help="List virtual machines")
    vm_list.add_argument("--limit", type=int, default=50, help="Max VMs to return")
    vm_list.add_argument("--json", action="store_true", help="Output as JSON")

    vm_info = vm_sub.add_parser("info", help="Get detailed information about a VM")
    vm_info.add_argument("--vm", required=True, help="Virtual machine name")
    vm_info.add_argument("--json", action="store_true", help="Output as JSON")

    # snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Snapshot / checkpoint operations")
    snap_sub = snap_parser.add_subparsers(dest="snap_action")

    snap_list = snap_sub.add_parser("list", help="List snapshots for a VM")
    snap_list.add_argument("--vm", required=True, help="Virtual machine name")
    snap_list.add_argument("--json", action="store_true", help="Output as JSON")

    snap_create = snap_sub.add_parser("create", help="Create a snapshot")
    snap_create.add_argument("--vm", required=True, help="Virtual machine name")
    snap_create.add_argument("--snap", required=True, help="Snapshot name")
    snap_create.add_argument("--desc", default="", help="Description")
    snap_create.add_argument("--json", action="store_true", help="Output as JSON")

    snap_delete = snap_sub.add_parser("delete", help="Delete a snapshot")
    snap_delete.add_argument("--vm", required=True, help="Virtual machine name")
    snap_delete.add_argument("--snap", required=True, help="Snapshot name")
    snap_delete.add_argument("--json", action="store_true", help="Output as JSON")

    # network
    net_parser = subparsers.add_parser("network", help="Virtual network operations")
    net_sub = net_parser.add_subparsers(dest="net_action")

    net_list = net_sub.add_parser("list", help="List virtual networks")
    net_list.add_argument("--json", action="store_true", help="Output as JSON")

    # host
    host_parser = subparsers.add_parser("host", help="Hypervisor host operations")
    host_sub = host_parser.add_subparsers(dest="host_action")

    host_info = host_sub.add_parser("info", help="Inspect host capabilities and active hypervisor")
    host_info.add_argument("--json", action="store_true", help="Output as JSON")

    # sandbox
    sb_parser = subparsers.add_parser("sandbox", help="Isolated ephemeral code sandbox")
    sb_sub = sb_parser.add_subparsers(dest="sb_action")

    sb_run = sb_sub.add_parser("run", help="Run code inside the sandbox")
    sb_run.add_argument("--code", required=True, help="Code string to execute")
    sb_run.add_argument("--lang", default="python", help="Language runtime (default: python)")
    sb_run.add_argument("--timeout", type=int, default=15, help="Execution timeout in seconds")
    sb_run.add_argument("--json", action="store_true", help="Output as JSON")

    # tools
    subparsers.add_parser("tools", help="List all verbs and tools JSON metadata")

    # mcp
    mcp_parser = subparsers.add_parser("mcp", help="Run MCP stdio server")
    mcp_parser.add_argument("--allow-path", default="", help="Confinement root path")

    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    if args.subcommand == "vm":
        if args.vm_action == "list":
            vms = list_vms()[: args.limit]
            if args.json:
                print(json.dumps({"success": True, "vms": [v.model_dump() for v in vms]}))
            else:
                for v in vms:
                    print(f"- {v.name} ({v.state}, {v.memory_mb} MB, {v.provider})")
        elif args.vm_action == "info":
            vm = get_vm_info(args.vm)
            if vm:
                if args.json:
                    print(json.dumps({"success": True, "vm_info": vm.model_dump()}))
                else:
                    for k, val in vm.model_dump().items():
                        print(f"  {k}: {val}")
            else:
                err = {"success": False, "error": f"VM '{args.vm}' not found"}
                if args.json:
                    print(json.dumps(err))
                else:
                    print(err["error"])
                sys.exit(1)
        else:
            vm_parser.print_help()

    elif args.subcommand == "snapshot":
        if args.snap_action == "list":
            snaps = list_snapshots(args.vm)
            if args.json:
                print(json.dumps({"success": True, "vm": args.vm, "snapshots": [s.model_dump() for s in snaps]}))
            else:
                print(f"Snapshots for {args.vm}:")
                for s in snaps:
                    print(f"  - {s.name} ({s.created})")
        elif args.snap_action == "create":
            snap = create_snapshot(args.vm, args.snap, args.desc)
            if args.json:
                print(json.dumps({"success": True, "snapshot": snap.model_dump()}))
            else:
                print(f"Created snapshot '{snap.name}' for {args.vm}")
        elif args.snap_action == "delete":
            ok = delete_snapshot(args.vm, args.snap)
            if args.json:
                print(json.dumps({"success": ok, "vm": args.vm, "deleted": args.snap}))
            else:
                print(f"Deleted snapshot '{args.snap}' from {args.vm}")
        else:
            snap_parser.print_help()

    elif args.subcommand == "network":
        if args.net_action == "list":
            nets = list_networks()
            if args.json:
                print(json.dumps({"success": True, "networks": [n.model_dump() for n in nets]}))
            else:
                for n in nets:
                    print(f"- {n.name} ({n.type}, {n.ip}/{n.netmask})")
        else:
            net_parser.print_help()

    elif args.subcommand == "host":
        if args.host_action == "info":
            hi = get_host_info()
            if args.json:
                print(json.dumps({"success": True, "host_info": hi.model_dump()}))
            else:
                for k, v in hi.model_dump().items():
                    print(f"{k}: {v}")
        else:
            host_parser.print_help()

    elif args.subcommand == "sandbox":
        if args.sb_action == "run":
            res = run_code_in_sandbox(args.code, args.lang, args.timeout)
            if args.json:
                print(json.dumps({"success": res.success, "result": res.model_dump()}))
            else:
                if res.stdout:
                    print(res.stdout, end="")
                if res.stderr:
                    print(res.stderr, file=sys.stderr, end="")
            if not res.success:
                sys.exit(res.returncode or 1)
        else:
            sb_parser.print_help()

    elif args.subcommand == "tools":
        tools_doc = {
            "app": "virtucraft",
            "version": __version__,
            "verbs": [
                {"name": "vm list", "description": "List virtual machines"},
                {"name": "vm info", "description": "Get detailed info for a virtual machine"},
                {"name": "snapshot list", "description": "List checkpoints/snapshots for a VM"},
                {"name": "snapshot create", "description": "Create a checkpoint/snapshot"},
                {"name": "snapshot delete", "description": "Delete a checkpoint/snapshot"},
                {"name": "network list", "description": "List virtual switches and networks"},
                {"name": "host info", "description": "Inspect host hypervisor and system telemetry"},
                {"name": "sandbox run", "description": "Run isolated ephemeral code snippet"},
            ],
        }
        print(json.dumps(tools_doc, indent=2))

    elif args.subcommand == "mcp":
        from .mcp_server import run_stdio_mcp

        run_stdio_mcp()


if __name__ == "__main__":
    main()
