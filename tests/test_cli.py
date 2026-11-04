"""Unit and CLI tests for VirtuCraft."""

import json
from virtucraft.cli import main
from virtucraft.hypervisor import get_host_info, list_vms, list_networks, create_snapshot, delete_snapshot
from virtucraft.sandbox import run_code_in_sandbox


def test_host_info():
    hi = get_host_info()
    assert hi.os in ("Windows", "Linux", "Darwin")
    assert hi.cpu_count > 0


def test_list_vms():
    vms = list_vms()
    assert len(vms) >= 1
    vm = vms[0]
    assert vm.name
    assert vm.state in ("Running", "Off", "Paused", "Saved")


def test_list_networks():
    nets = list_networks()
    assert len(nets) >= 1
    assert nets[0].name


def test_snapshot_roundtrip():
    vms = list_vms()
    target_vm = vms[0].name
    snap = create_snapshot(target_vm, "test-snap-ci", "automated CI test")
    assert snap.name == "test-snap-ci"
    assert snap.vm == target_vm

    deleted = delete_snapshot(target_vm, "test-snap-ci")
    assert deleted is True


def test_sandbox_run():
    res = run_code_in_sandbox("print('hello-virtucraft')")
    assert res.success is True
    assert "hello-virtucraft" in res.stdout
    assert res.returncode == 0
