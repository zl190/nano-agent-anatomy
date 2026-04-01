"""
E2E smoke tests — verifies the full agent actually runs against the API.
Requires ANTHROPIC_API_KEY. Skipped in CI without it.

These are NOT unit tests. They hit the real API and cost ~$0.01 per run.
Purpose: catch "tests pass but code doesn't work" gaps.
"""

import os
import subprocess
import sys
import unittest

NEEDS_KEY = not os.environ.get("ANTHROPIC_API_KEY")
SKIP_MSG = "ANTHROPIC_API_KEY not set"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_agent(args: list[str], stdin_text: str, timeout: int = 60) -> str:
    """Run main.py with given args and piped input."""
    cmd = [sys.executable, "main.py"] + args
    result = subprocess.run(
        cmd, input=stdin_text, capture_output=True, text=True,
        cwd=PROJECT_ROOT, timeout=timeout,
    )
    return result.stdout + result.stderr


@unittest.skipIf(NEEDS_KEY, SKIP_MSG)
class TestBasicLoop(unittest.TestCase):
    def test_simple_question_returns_answer(self):
        output = run_agent([], "What is 2+2?\n")
        self.assertIn("4", output)

    def test_tool_call_works(self):
        output = run_agent([], "Run: echo hello_test_marker\n")
        self.assertIn("hello_test_marker", output)


@unittest.skipIf(NEEDS_KEY, SKIP_MSG)
class TestMemoryMode(unittest.TestCase):
    def test_memory_flag_runs(self):
        output = run_agent(["--memory"], "What is 3+3?\n")
        self.assertIn("6", output)


@unittest.skipIf(NEEDS_KEY, SKIP_MSG)
class TestCompressMode(unittest.TestCase):
    def test_compress_flag_runs(self):
        output = run_agent(["--memory", "--compress"], "What is 5+5?\n")
        self.assertIn("10", output)


@unittest.skipIf(NEEDS_KEY, SKIP_MSG)
class TestCoordinatorMode(unittest.TestCase):
    def test_coordinate_produces_result(self):
        output = run_agent(
            ["--coordinate", "What is the value of pi to 2 decimal places?"],
            "", timeout=120,
        )
        self.assertIn("3.14", output)


@unittest.skipIf(NEEDS_KEY, SKIP_MSG)
class TestCorrectionMicrocompactFunctional(unittest.TestCase):
    """Functional test: does correction-aware compaction actually change behavior?

    This is NOT a unit test. It verifies the educational claim:
    "compaction produces correct answers with fewer messages."
    """

    def test_compaction_gives_correct_answer_with_fewer_messages(self):
        sys.path.insert(0, PROJECT_ROOT)
        from context_v4 import correction_microcompact
        from anthropic import Anthropic

        client = Anthropic()
        model = "claude-haiku-4-5-20251001"

        def ask(msgs, q):
            msgs.append({"role": "user", "content": q})
            r = client.messages.create(model=model, max_tokens=100, messages=msgs)
            reply = r.content[0].text
            msgs.append({"role": "assistant", "content": reply})
            return reply

        # WITHOUT compaction
        msgs_base = []
        ask(msgs_base, "Remember: capital of Australia is Sydney.")
        ask(msgs_base, "What is the capital of Australia?")
        ask(msgs_base, "Wrong. The capital is Canberra.")
        ans_base = ask(msgs_base, "So what is the capital of Australia?")

        # WITH compaction
        msgs_comp = []
        ask(msgs_comp, "Remember: capital of Australia is Sydney.")
        ask(msgs_comp, "What is the capital of Australia?")
        correction = "Wrong. The capital is Canberra."
        msgs_comp, did = correction_microcompact(msgs_comp, correction)
        self.assertTrue(did, "Compaction should fire")
        ans_comp = ask(msgs_comp, "So what is the capital of Australia?")

        # Both should say Canberra
        self.assertIn("canberra", ans_comp.lower(),
                       f"Compacted answer should mention Canberra, got: {ans_comp}")
        # Compacted should use fewer messages
        self.assertLess(len(msgs_comp), len(msgs_base),
                        f"Compacted ({len(msgs_comp)}) should be fewer than baseline ({len(msgs_base)})")


if __name__ == "__main__":
    unittest.main()
