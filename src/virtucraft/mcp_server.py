"""FastMCP stdio server for VirtuCraft."""

from __future__ import annotations

import os
from typing import Any
from fastmcp import FastMCP

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

mcp = FastMCP("virtucraft")


@mcp.tool()
def vm_list(limit: int = 50) -> dict[str, Any]:
    """List virtual machines registered on the hypervisor or simulation."""
    vms = list_vms()[:limit]
    return {"success": True, "vms": [v.model_dump() for v in vms]}


@mcp.tool()
def vm_info(vm_name: str) -> dict[str, Any]:
    """Get detailed information about a virtual machine."""
    vm = get_vm_info(vm_name)
    if not vm:
        return {"success": False, "error": f"VM '{vm_name}' not found"}
    return {"success": True, "vm_info": vm.model_dump()}


@mcp.tool()
def snapshot_list(vm_name: str) -> dict[str, Any]:
    """List snapshots/checkpoints for a virtual machine."""
    snaps = list_snapshots(vm_name)
    return {"success": True, "vm": vm_name, "snapshots": [s.model_dump() for s in snaps]}


@mcp.tool()
def snapshot_create(vm_name: str, snap_name: str, description: str = "") -> dict[str, Any]:
    """Create a checkpoint or snapshot for a virtual machine."""
    snap = create_snapshot(vm_name, snap_name, description)
    return {"success": True, "snapshot": snap.model_dump()}


@mcp.tool()
def snapshot_delete(vm_name: str, snap_name: str) -> dict[str, Any]:
    """Delete a checkpoint or snapshot from a virtual machine."""
    ok = delete_snapshot(vm_name, snap_name)
    return {"success": ok, "vm": vm_name, "deleted": snap_name}


@mcp.tool()
def network_list() -> dict[str, Any]:
    """List virtual switches and networks."""
    nets = list_networks()
    return {"success": True, "networks": [n.model_dump() for n in nets]}


@mcp.tool()
def host_info() -> dict[str, Any]:
    """Inspect hypervisor host system capabilities and telemetry."""
    hi = get_host_info()
    return {"success": True, "host_info": hi.model_dump()}


@mcp.tool()
def sandbox_run(code: str, language: str = "python", timeout: int = 15) -> dict[str, Any]:
    """Run an isolated ephemeral code snippet inside the sandbox."""
    res = run_code_in_sandbox(code, language, timeout)
    return {"success": res.success, "result": res.model_dump()}


def run_stdio_mcp() -> None:
    """Run FastMCP over stdio transport."""
    os.environ["FASTMCP_BANNER"] = "0"
    mcp.run(transport="stdio")
