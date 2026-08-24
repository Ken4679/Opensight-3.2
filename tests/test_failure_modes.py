import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from opensight.core.safety import PortablePaths
from opensight.core.models import LogicalNode, Endpoint
from opensight.vpn.openvpn_process import OpenVPNProcessManager, VPNConnectionState
from opensight.vpn.credentials import OpenVPNCredentials

@pytest.fixture
def temp_paths(tmp_path):
    base = tmp_path / "opensight_portable"
    base.mkdir(parents=True, exist_ok=True)
    profiles = base / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    data = base / "data"
    data.mkdir(parents=True, exist_ok=True)
    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return PortablePaths(
        base_dir=base,
        profiles_dir=profiles,
        data_dir=data,
        logs_dir=logs,
        openvpn_dir=base / "openvpn",
        singbox_dir=base / "singbox",
        is_isolated=True,
    )

def test_vpn_state_starts_disconnected(temp_paths):
    mgr = OpenVPNProcessManager(temp_paths)
    assert mgr.get_state() == VPNConnectionState.DISCONNECTED
    assert not mgr.is_connected()

def test_vpn_disconnect_idempotent(temp_paths):
    mgr = OpenVPNProcessManager(temp_paths)
    # Calling disconnect when already disconnected should not throw and remain safe
    mgr.disconnect()
    assert mgr.get_state() == VPNConnectionState.DISCONNECTED
    mgr.disconnect()
    assert mgr.get_state() == VPNConnectionState.DISCONNECTED

def test_vpn_connect_with_missing_ovpn_file(temp_paths):
    mgr = OpenVPNProcessManager(temp_paths)
    fake_node = LogicalNode(
        id="test_node_missing",
        server_name="Missing Node",
        country="JP",
        city="Tokyo",
        endpoints=[Endpoint(ip_or_domain="1.2.3.4", port=443, protocol="tcp", profile_path=str(temp_paths.profiles_dir / "non_existent.ovpn"))],
        primary_endpoint=Endpoint(ip_or_domain="1.2.3.4", port=443, protocol="tcp", profile_path=str(temp_paths.profiles_dir / "non_existent.ovpn"))
    )

    creds = OpenVPNCredentials(username="user", password="pwd")
    ok = mgr.connect(fake_node, creds)
    # Must fail safely without crash and return False, entering FAILED or DISCONNECTED state
    assert not ok
    assert mgr.get_state() in (VPNConnectionState.FAILED, VPNConnectionState.DISCONNECTED)

def test_vpn_connect_with_malformed_ovpn(temp_paths):
    # Malformed OVPN containing dangerous directive
    bad_ovpn = temp_paths.profiles_dir / "malicious.ovpn"
    bad_ovpn.write_text("client\ndev tun\nscript-security 2\nup /bin/sh\n", encoding="utf-8")

    mgr = OpenVPNProcessManager(temp_paths)
    fake_node = LogicalNode(
        id="bad_node",
        server_name="Bad Node",
        country="US",
        city="LA",
        endpoints=[Endpoint(ip_or_domain="1.2.3.4", port=443, protocol="tcp", profile_path=str(bad_ovpn))],
        primary_endpoint=Endpoint(ip_or_domain="1.2.3.4", port=443, protocol="tcp", profile_path=str(bad_ovpn))
    )

    creds = OpenVPNCredentials(username="user", password="pwd")
    ok = mgr.connect(fake_node, creds)
    # Security validation must block it
    assert not ok
    assert mgr.get_state() in (VPNConnectionState.FAILED, VPNConnectionState.DISCONNECTED)

def test_vpn_killswitch_failure_resilience(temp_paths):
    mgr = OpenVPNProcessManager(temp_paths)
    # Mock leak guard failure
    with patch.object(mgr._leak_guard, "install_app_kill_switch", return_value=False):
        mgr.configure_kill_switch(["C:\\app\\test.exe"])
        result = mgr.enable_kill_switch()
        assert result is False
        # State reflects actual failure
        assert mgr.is_kill_switch_active() is False

    # Mock clean disable
    with patch.object(mgr._leak_guard, "remove_app_kill_switch", return_value=True):
        disable_result = mgr.disable_kill_switch()
        assert disable_result is True
        assert mgr.is_kill_switch_active() is False
