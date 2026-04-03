"""Smoke tests for the MCP server scaffold."""

import pytest

mcp = pytest.importorskip("mcp")

from gongmun_doctor.mcp.server import create_mcp_server


def test_create_mcp_server():
    server = create_mcp_server()

    assert server is not None
