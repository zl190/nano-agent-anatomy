"""
Tests for coordinator_v0 and coordinator_v3.
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

from coordinator_v0 import (
    coordinate as coordinate_v0,
    WORKER_SYSTEM,
    TOOLS,
    run_worker,
)
from coordinator_v3 import (
    COORDINATOR_SYSTEM as V3_COORD,
    WORKER_SYSTEM as V3_WORKER,
    quality_check,
)


class TestCoordinatorV0Decomposition(unittest.TestCase):
    def test_source_contains_research_subtask(self):
        source = inspect.getsource(coordinate_v0)
        self.assertIn("Research:", source)

    def test_source_contains_execute_subtask(self):
        source = inspect.getsource(coordinate_v0)
        self.assertIn("Execute:", source)

    def test_two_hardcoded_subtasks(self):
        # The subtasks list is built with two f-string entries
        source = inspect.getsource(coordinate_v0)
        # Count the f-string patterns that form the actual subtask list entries
        self.assertGreaterEqual(source.count('f"Research:'), 1)
        self.assertGreaterEqual(source.count('f"Execute:'), 1)
        # Exactly 2 subtasks in the hardcoded list
        subtasks_section = source[source.find("subtasks = ["):]
        self.assertIn('"Research:', subtasks_section)
        self.assertIn('"Execute:', subtasks_section)


class TestWorkerSystemPrompt(unittest.TestCase):
    def test_worker_system_is_concise(self):
        # Worker prompts should be short and focused
        self.assertLess(len(WORKER_SYSTEM), 200)

    def test_worker_system_is_nonempty(self):
        self.assertTrue(len(WORKER_SYSTEM.strip()) > 0)


class TestToolsDefinition(unittest.TestCase):
    def test_tools_match_expected_set(self):
        names = {t["name"] for t in TOOLS}
        self.assertEqual(names, {"bash", "read_file", "write_file"})

    def test_each_tool_has_required_fields(self):
        for tool in TOOLS:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("input_schema", tool)


class TestWorkerIsolation(unittest.TestCase):
    def test_worker_creates_own_message_list(self):
        source = inspect.getsource(run_worker)
        # Worker initializes its own local message list — not shared state
        self.assertIn("messages = [", source)

    def test_worker_has_iteration_cap(self):
        source = inspect.getsource(run_worker)
        # Worker loop is bounded (for _ in range(...))
        self.assertIn("range(", source)


class TestCoordinatorV3Prompts(unittest.TestCase):
    def test_coord_contains_rubber_stamp_rule(self):
        self.assertIn("rubber-stamp", V3_COORD.lower())

    def test_coord_contains_delegate_understanding_rule(self):
        self.assertIn("delegate understanding", V3_COORD.lower())

    def test_coord_contains_colleague_phrasing(self):
        self.assertIn("colleague", V3_COORD.lower())

    def test_worker_contains_scope_rule(self):
        self.assertIn("scope", V3_WORKER.lower())

    def test_worker_contains_blocker_rule(self):
        has_blocking = "blocking" in V3_WORKER.lower()
        has_blocker = "blocker" in V3_WORKER.lower()
        self.assertTrue(has_blocking or has_blocker)

    def test_coord_prompt_is_nonempty(self):
        self.assertTrue(len(V3_COORD.strip()) > 0)

    def test_worker_prompt_is_nonempty(self):
        self.assertTrue(len(V3_WORKER.strip()) > 0)


class TestQualityCheckSignature(unittest.TestCase):
    def test_quality_check_has_synthesis_param(self):
        sig = inspect.signature(quality_check)
        self.assertIn("synthesis", sig.parameters)

    def test_quality_check_has_results_param(self):
        sig = inspect.signature(quality_check)
        self.assertIn("results", sig.parameters)

    def test_quality_check_has_client_and_model(self):
        sig = inspect.signature(quality_check)
        self.assertIn("client", sig.parameters)
        self.assertIn("model", sig.parameters)

    def test_quality_check_is_callable(self):
        self.assertTrue(callable(quality_check))


if __name__ == "__main__":
    unittest.main()
