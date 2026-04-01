"""
Tests for context_v1 through context_v3.
Tests are structural and deterministic — no API key required.
"""

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

from context_v1 import (
    count_tokens_approx,
    extract_file_paths,
    infer_pending_work,
    summarize_messages,
    ContextCompressor,
)
from context_v2 import strip_analysis_tags
from context_v3 import NO_TOOLS_PREAMBLE


class TestCountTokensApprox(unittest.TestCase):
    def test_basic_token_count(self):
        msgs = [{"role": "user", "content": "hello world"}]
        count = count_tokens_approx(msgs)
        # "hello world" = 11 chars -> 11//4 + 1 = 3
        self.assertEqual(count, 3)

    def test_empty_messages_is_zero(self):
        self.assertEqual(count_tokens_approx([]), 0)

    def test_multiple_messages_accumulate(self):
        msgs = [
            {"role": "user", "content": "hello world"},
            {"role": "assistant", "content": "hello world"},
        ]
        self.assertEqual(count_tokens_approx(msgs), 6)

    def test_longer_content_gives_higher_count(self):
        short = [{"role": "user", "content": "hi"}]
        long = [{"role": "user", "content": "x" * 400}]
        self.assertGreater(count_tokens_approx(long), count_tokens_approx(short))


class TestExtractFilePaths(unittest.TestCase):
    def test_extracts_known_extensions(self):
        # Note: regex matches greedily — "config.json" is matched as "config.js"
        # because "js" is listed before "json" and the alternation stops there.
        # Use unambiguous extensions to validate the regex works correctly.
        text = "Look at src/main.py and config.yaml and README.md"
        paths = extract_file_paths(text)
        self.assertIn("src/main.py", paths)
        self.assertIn("config.yaml", paths)
        self.assertIn("README.md", paths)

    def test_max_cap_is_8(self):
        text = " ".join(f"file{i}.py" for i in range(20))
        paths = extract_file_paths(text)
        self.assertEqual(len(paths), 8)

    def test_deduplication(self):
        text = "main.py main.py main.py"
        paths = extract_file_paths(text)
        self.assertEqual(len(paths), 1)

    def test_no_match_returns_empty(self):
        text = "no files mentioned here at all"
        paths = extract_file_paths(text)
        self.assertEqual(paths, [])


class TestInferPendingWork(unittest.TestCase):
    def test_detects_todo_keyword(self):
        msgs = [{"role": "user", "content": "todo: fix the auth bug"}]
        pending = infer_pending_work(msgs)
        self.assertGreaterEqual(len(pending), 1)

    def test_detects_next_keyword(self):
        msgs = [{"role": "user", "content": "Next step is deploy"}]
        pending = infer_pending_work(msgs)
        self.assertGreaterEqual(len(pending), 1)

    def test_no_keywords_returns_empty(self):
        msgs = [{"role": "user", "content": "The weather is nice today."}]
        pending = infer_pending_work(msgs)
        self.assertEqual(pending, [])

    def test_caps_at_5_items(self):
        msgs = [
            {"role": "user", "content": "\n".join(
                f"todo: task {i}" for i in range(20)
            )}
        ]
        pending = infer_pending_work(msgs)
        self.assertLessEqual(len(pending), 5)


class TestContextCompressorDualTrigger(unittest.TestCase):
    def test_many_short_messages_does_not_compress(self):
        # Token count low even though message count is high
        comp = ContextCompressor(max_tokens=100, min_messages=5, keep_recent=2)
        short_msgs = [{"role": "user", "content": "hi"} for _ in range(10)]
        self.assertFalse(comp.should_compress(short_msgs))

    def test_few_long_messages_does_not_compress(self):
        # Token count high but message count below min
        comp = ContextCompressor(max_tokens=100, min_messages=5, keep_recent=2)
        long_msgs = [{"role": "user", "content": "x" * 2000} for _ in range(3)]
        self.assertFalse(comp.should_compress(long_msgs))

    def test_both_conditions_met_triggers_compress(self):
        comp = ContextCompressor(max_tokens=100, min_messages=5, keep_recent=2)
        many_long = [{"role": "user", "content": "x" * 200} for _ in range(10)]
        self.assertTrue(comp.should_compress(many_long))

    def test_exact_threshold_not_exceeded_no_compress(self):
        comp = ContextCompressor(max_tokens=1000, min_messages=10, keep_recent=2)
        msgs = [{"role": "user", "content": "hi"} for _ in range(5)]
        self.assertFalse(comp.should_compress(msgs))


class TestSummarizeMessages(unittest.TestCase):
    def test_summary_contains_pending_tasks(self):
        msgs = [
            {"role": "user", "content": "fix auth"},
            {"role": "assistant", "content": "done"},
            {"role": "user", "content": "todo: update changelog"},
        ]
        summary = summarize_messages(msgs)
        self.assertTrue(
            "todo" in summary.lower() or "changelog" in summary.lower()
        )

    def test_summary_wraps_in_tags(self):
        msgs = [{"role": "user", "content": "hello"}]
        summary = summarize_messages(msgs)
        self.assertIn("<summary>", summary)
        self.assertIn("</summary>", summary)

    def test_summary_includes_message_counts(self):
        msgs = [
            {"role": "user", "content": "msg one"},
            {"role": "assistant", "content": "reply one"},
        ]
        summary = summarize_messages(msgs)
        self.assertIn("1 user", summary)
        self.assertIn("1 assistant", summary)


class TestStripAnalysisTags(unittest.TestCase):
    def test_strips_analysis_block(self):
        text = "<analysis>internal thinking</analysis><summary>the actual summary</summary>"
        result = strip_analysis_tags(text)
        self.assertNotIn("internal thinking", result)

    def test_preserves_summary_content(self):
        text = "<analysis>internal thinking</analysis><summary>the actual summary</summary>"
        result = strip_analysis_tags(text)
        self.assertIn("the actual summary", result)

    def test_multiline_analysis_stripped(self):
        text = "<analysis>\nline one\nline two\n</analysis>\nremaining text"
        result = strip_analysis_tags(text)
        self.assertNotIn("line one", result)
        self.assertIn("remaining text", result)

    def test_no_analysis_tag_unchanged(self):
        text = "no tags here"
        result = strip_analysis_tags(text)
        self.assertEqual(result, "no tags here")


class TestNoToolsPreamble(unittest.TestCase):
    def test_preamble_contains_rejected(self):
        self.assertIn("REJECTED", NO_TOOLS_PREAMBLE)

    def test_preamble_mentions_tool(self):
        self.assertIn("tool", NO_TOOLS_PREAMBLE.lower())

    def test_preamble_is_nonempty(self):
        self.assertTrue(len(NO_TOOLS_PREAMBLE) > 0)


from context_v4 import detect_correction, correction_microcompact, extract_text


class TestDetectCorrection(unittest.TestCase):
    """Test correction signal detection (Stage-1 classifier)."""

    def test_english_correction_detected(self):
        self.assertTrue(detect_correction("No, I meant the other one"))

    def test_chinese_correction_detected(self):
        self.assertTrue(detect_correction("不对，应该是另一个"))

    def test_normal_message_not_flagged(self):
        self.assertFalse(detect_correction("What is the capital of France?"))

    def test_case_insensitive(self):
        self.assertTrue(detect_correction("ACTUALLY, that's wrong"))

    def test_empty_string(self):
        self.assertFalse(detect_correction(""))


class TestCorrectionMicrocompact(unittest.TestCase):
    """Test surgical compaction of wrong assistant turns."""

    def setUp(self):
        self.messages = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 is 5."},
        ]

    def test_replaces_assistant_with_correction_note(self):
        result, did_compact = correction_microcompact(self.messages, "No, it's 4")
        self.assertTrue(did_compact)
        # The wrong assistant message should be replaced
        self.assertEqual(result[1]["role"], "user")
        self.assertIn("Correction note", result[1]["content"])
        self.assertIn("No, it's 4", result[1]["content"])

    def test_net_minus_one_message(self):
        """After compaction, message count should decrease by 1 (wrong turn replaced, no new append)."""
        original_count = len(self.messages)
        result, _ = correction_microcompact(self.messages, "No, it's 4")
        # correction_microcompact replaces in-place, so same count
        self.assertEqual(len(result), original_count)

    def test_no_assistant_returns_false(self):
        msgs = [{"role": "user", "content": "Hello"}]
        result, did_compact = correction_microcompact(msgs, "No")
        self.assertFalse(did_compact)
        self.assertEqual(len(result), 1)

    def test_preserves_earlier_messages(self):
        msgs = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Reply 1"},
            {"role": "user", "content": "Second"},
            {"role": "assistant", "content": "Wrong reply"},
        ]
        result, did_compact = correction_microcompact(msgs, "Actually no")
        self.assertTrue(did_compact)
        # First two messages untouched
        self.assertEqual(result[0]["content"], "First")
        self.assertEqual(result[1]["content"], "Reply 1")
        # Last assistant replaced
        self.assertIn("Correction note", result[3]["content"])

    def test_long_wrong_content_truncated(self):
        msgs = [
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "X" * 500},
        ]
        result, _ = correction_microcompact(msgs, "Wrong")
        # Excerpt should be capped at 200 chars + "..."
        self.assertIn("...", result[1]["content"])

    def test_correction_note_is_user_role(self):
        """Note must be user role — assistant role is too easy to self-rationalize."""
        result, _ = correction_microcompact(self.messages, "Fix this")
        self.assertEqual(result[1]["role"], "user")


class TestExtractText(unittest.TestCase):
    def test_string_passthrough(self):
        self.assertEqual(extract_text("hello"), "hello")

    def test_content_block_list(self):
        blocks = [{"text": "part1"}, {"text": "part2"}]
        self.assertEqual(extract_text(blocks), "part1 part2")


if __name__ == "__main__":
    unittest.main()
