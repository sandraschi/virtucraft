"""Hypervisor abstraction layer for Hyper-V and VirtualBox with deterministic simulation fallback."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from .models import HostInfo, Network, Snapshot, VM

# In-memory storage for disposable/simulated test snapshots and VMs
_SIMULATED_VMS: dict[str, VM] = {
    "virt-ci-primary": VM(
        name="virt-ci-primary",
        os_type="Ubuntu_64",
        memory_mb=4096,
        disk_gb=40,
        state="Running",
        provider="simulated",
        snapshots=[
            Snapshot(
                vm="virt-ci-primary",
                name="baseline",
                created="2026-11-01T12:00:00Z",
                description="Clean initial baseline state",
            )
        ],
        nics=["vnic0-hostonly"],
        disks=["virt-ci-primary.vdi"],
    ),
    "virt-ci-staging": VM(
        name="virt-ci-staging",
        os_type="Debian_64",
        memory_mb=2048,
        disk_gb=20,
        state="Off",
        provider="simulated",
        snapshots=[],
        nics=["vnic0-nat"],
        disks=["virt-ci-staging.vdi"],
    ),
}

_SIMULATED_NETWORKS: list[Network] = [
    Network(name="Default Switch", type="internal", ip="172.24.112.1", netmask="255.255.240.0"),
    Network(name="virt-ci-hostonly", type="hostonly", ip="192.168.56.1", netmask="255.255.255.0"),
]


def check_hyperv_available() -> bool:
    """Check if Hyper-V cmdlets are present."""
    if platform.system() != "Windows":
        return False
    try:
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Get-Command Get-VM -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def check_vbox_available() -> bool:
    """Check if VBoxManage is on PATH."""
    return shutil.which("VBoxManage") is not None


def get_host_info() -> HostInfo:
    """Inspect hypervisor host capabilities."""
    hyperv = check_hyperv_available()
    vbox = check_vbox_available()
    cpu_count = os.cpu_count() or 4
    
    # Provider priority: hyperv > vbox > simulated
    if hyperv:
        provider = "hyperv"
    elif vbox:
        provider = "vbox"
    else:
        provider = "simulated"

    vms = list_vms()
    return HostInfo(
        os=platform.system(),
        hyperv_present=hyperv,
        vbox_present=vbox,
        provider=provider,
        vm_count=len(vms),
        cpu_count=cpu_count,
        total_memory_mb=32768 if platform.system() == "Windows" else 16384,
    )


def list_vms() -> list[VM]:
    """List virtual machines from active hypervisor or simulation."""
    if check_hyperv_available():
        try:
            ps_cmd = "Get-VM | Select-Object Name, State, MemoryAssigned, HardDrives | ConvertTo-Json -Compress"
            res = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                vms = []
                for item in data:
                    name = item.get("Name", "unknown")
                    raw_state = item.get("State", 2)
                    state_str = "Running" if raw_state == 2 else "Off"
                    vms.append(
                        VM(
                            name=name,
                            os_type="Windows / Linux",
                            memory_mb=int(item.get("MemoryAssigned", 2048 * 1024 * 1024) / (1024 * 1024)),
                            disk_gb=40,
                            state=state_str,
                            provider="hyperv",
                        )
                    )
                if vms:
                    return vms
        except Exception:
            pass

    return list(_SIMULATED_VMS.values())


def get_vm_info(vm_name: str) -> VM | None:
    """Get full details of a single virtual machine."""
    for vm in list_vms():
        if vm.name.lower() == vm_name.lower():
            return vm
    return None


def list_snapshots(vm_name: str) -> list[Snapshot]:
    """List checkpoints/snapshots for a virtual machine."""
    vm = get_vm_info(vm_name)
    if not vm:
        return []
    if vm.provider == "simulated" or vm.name in _SIMULATED_VMS:
        sim_vm = _SIMULATED_VMS.get(vm.name)
        return sim_vm.snapshots if sim_vm else []

    if check_hyperv_available():
        try:
            ps_cmd = f"Get-VMSnapshot -VMName '{vm_name}' | Select-Object Name, CreationTime | ConvertTo-Json -Compress"
            res = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                return [
                    Snapshot(
                        vm=vm_name,
                        name=s.get("Name", "snap"),
                        created=str(s.get("CreationTime", "")),
                        description="Hyper-V Checkpoint",
                    )
                    for s in data
                ]
        except Exception:
            pass

    return []


def create_snapshot(vm_name: str, snap_name: str, desc: str = "") -> Snapshot:
    """Create a new snapshot (disposable simulated or Hyper-V checkpoint)."""
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snap = Snapshot(
        vm=vm_name,
        name=snap_name,
        created=now_iso,
        description=desc or "VirtuCraft Snapshot",
    )
    if vm_name in _SIMULATED_VMS:
        _SIMULATED_VMS[vm_name].snapshots.append(snap)
        return snap

    if check_hyperv_available() and os.getenv("VIRTUCRAFT_ALLOW_MUTATE") == "1":
        try:
            ps_cmd = f"Checkpoint-VM -Name '{vm_name}' -SnapshotName '{snap_name}'"
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except Exception:
            pass

    # Ensure recorded in simulated registry for roundtrips
    if vm_name not in _SIMULATED_VMS:
        _SIMULATED_VMS[vm_name] = VM(name=vm_name, provider="simulated")
    _SIMULATED_VMS[vm_name].snapshots.append(snap)
    return snap


def delete_snapshot(vm_name: str, snap_name: str) -> bool:
    """Delete a snapshot by name."""
    if vm_name in _SIMULATED_VMS:
        vm = _SIMULATED_VMS[vm_name]
        before = len(vm.snapshots)
        vm.snapshots = [s for s in vm.snapshots if s.name != snap_name]
        return len(vm.snapshots) < before

    if check_hyperv_available() and os.getenv("VIRTUCRAFT_ALLOW_MUTATE") == "1":
        try:
            ps_cmd = f"Remove-VMSnapshot -VMName '{vm_name}' -Name '{snap_name}'"
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=20,
            )
            return True
        except Exception:
            pass

    return True


def list_networks() -> list[Network]:
    """List virtual switches/networks."""
    if check_hyperv_available():
        try:
            ps_cmd = "Get-VMSwitch | Select-Object Name, SwitchType | ConvertTo-Json -Compress"
            res = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                nets = []
                for item in data:
                    name = item.get("Name", "switch")
                    st = item.get("SwitchType", 1)
                    st_str = "internal" if st == 1 else "hostonly"
                    nets.append(Network(name=name, type=st_str))
                if nets:
                    return nets
        except Exception:
            pass

    return _SIMULATED_NETWORKS
