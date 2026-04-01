"""
Tests for loop_v0 through loop_v3.
Tests are structural and deterministic — no API key required.
"""

import inspect
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Stub out the anthropic module before any project code imports it
_anthropic_stub = types.ModuleType("anthropic")
_anthropic_stub.Anthropic = MagicMock
sys.modules.setdefault("anthropic", _anthropic_stub)

from loop_v0 import execute_tool
from loop_v1 import is_bash_denied, MAX_ITERATIONS
from loop_v2 import run_turn
from permissions import PermissionPolicy, PermissionMode, TOOL_PERMISSIONS


class TestIsBashDenied(unittest.TestCase):
    def test_rm_rf_root_is_denied(self):
        self.assertTrue(is_bash_denied("rm -rf /"))

    def test_safe_command_is_allowed(self):
        self.assertFalse(is_bash_denied("ls -la"))

    def test_substring_match_in_echo(self):
        # Substring match: even inside an echo, rm -rf is blocked
        self.assertTrue(is_bash_denied("echo rm -rf test"))

    def test_empty_string_is_allowed(self):
        self.assertFalse(is_bash_denied(""))

    def test_partial_rm_without_flag_is_allowed(self):
        self.assertFalse(is_bash_denied("rm file.txt"))


class TestMaxIterations(unittest.TestCase):
    def test_max_iterations_is_16(self):
        self.assertEqual(MAX_ITERATIONS, 16)


class TestExecuteTool(unittest.TestCase):
    def test_read_file_not_found_returns_error(self):
        result = execute_tool("read_file", {"path": "/nonexistent/path/file.txt"})
        self.assertIn("Error", result)

    def test_unknown_tool_returns_error(self):
        result = execute_tool("unknown_tool", {})
        self.assertIn("Error", result)

    def test_unknown_tool_mentions_tool_name(self):
        result = execute_tool("my_custom_tool", {})
        self.assertIn("my_custom_tool", result)

    def test_bash_timeout_returns_error(self):
        # A fast-running command should succeed and not return an error prefix
        result = execute_tool("bash", {"command": "echo hello"})
        self.assertIn("hello", result)


class TestRunTurnSignature(unittest.TestCase):
    def test_run_turn_accepts_token_budget(self):
        sig = inspect.signature(run_turn)
        self.assertIn("token_budget", sig.parameters)

    def test_run_turn_token_budget_has_default(self):
        sig = inspect.signature(run_turn)
        param = sig.parameters["token_budget"]
        self.assertIsNot(param.default, inspect.Parameter.empty)

    def test_run_turn_required_params(self):
        sig = inspect.signature(run_turn)
        params = list(sig.parameters.keys())
        for required in ("client", "model", "system", "messages"):
            self.assertIn(required, params)


class TestPermissionIntegration(unittest.TestCase):
    def test_unknown_tool_denied_in_read_only(self):
        policy = PermissionPolicy(PermissionMode.READ_ONLY)
        allowed, reason = policy.authorize("unknown_tool", {})
        self.assertFalse(allowed)
        self.assertIn("DANGER_FULL_ACCESS", reason)

    def test_read_file_allowed_in_read_only(self):
        policy = PermissionPolicy(PermissionMode.READ_ONLY)
        allowed, _ = policy.authorize("read_file", {})
        self.assertTrue(allowed)

    def test_write_file_denied_in_read_only(self):
        policy = PermissionPolicy(PermissionMode.READ_ONLY)
        allowed, reason = policy.authorize("write_file", {})
        self.assertFalse(allowed)
        self.assertIn("WORKSPACE_WRITE", reason)

    def test_write_file_allowed_in_workspace_write(self):
        policy = PermissionPolicy(PermissionMode.WORKSPACE_WRITE)
        allowed, _ = policy.authorize("write_file", {})
        self.assertTrue(allowed)

    def test_bash_denied_in_workspace_write(self):
        policy = PermissionPolicy(PermissionMode.WORKSPACE_WRITE)
        allowed, _ = policy.authorize("bash", {})
        self.assertFalse(allowed)

    def test_bash_allowed_in_danger_full_access(self):
        policy = PermissionPolicy(PermissionMode.DANGER_FULL_ACCESS)
        allowed, _ = policy.authorize("bash", {})
        self.assertTrue(allowed)

    def test_tool_permissions_map_has_three_tools(self):
        self.assertIn("read_file", TOOL_PERMISSIONS)
        self.assertIn("write_file", TOOL_PERMISSIONS)
        self.assertIn("bash", TOOL_PERMISSIONS)


if __name__ == "__main__":
    unittest.main()
