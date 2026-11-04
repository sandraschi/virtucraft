"""Domain models for VirtuCraft."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class Snapshot(BaseModel):
    vm: str
    name: str
    created: str = ""
    description: str = ""


class Network(BaseModel):
    name: str
    type: str = "hostonly"  # nat, bridged, hostonly, internal
    ip: str = "192.168.56.1"
    netmask: str = "255.255.255.0"


class VM(BaseModel):
    name: str
    os_type: str = "Windows"
    memory_mb: int = 2048
    disk_gb: int = 40
    state: str = "Off"  # Running, Off, Paused, Saved
    provider: str = "hyperv"  # hyperv, vbox, simulated
    snapshots: list[Snapshot] = Field(default_factory=list)
    nics: list[str] = Field(default_factory=list)
    disks: list[str] = Field(default_factory=list)


class HostInfo(BaseModel):
    os: str = "Windows"
    hyperv_present: bool = False
    vbox_present: bool = False
    provider: str = "hyperv"
    vm_count: int = 0
    total_memory_mb: int = 16384
    cpu_count: int = 8


class SandboxResult(BaseModel):
    success: bool
    language: str
    code: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    ms: int = 0
