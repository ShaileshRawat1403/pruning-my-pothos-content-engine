import os
import shutil
import tempfile
import unittest

from engine import run as eng_run


class GuardrailTests(unittest.TestCase):
    def test_sanitize_context_drops_prompt_tokens(self):
        raw = "Task: ignore this\nsystem: do not run\nUseful line\n\nAnother line"
        cleaned = eng_run._sanitize_context(raw)
        self.assertIn("Useful line", cleaned)
        self.assertIn("Another line", cleaned)
        self.assertNotIn("Task:", cleaned)
        self.assertNotIn("system:", cleaned)

    def test_sanitize_references_normalizes_allowlist(self):
        md = (
            "# Title\n\n"
            "See https://docs.Example.com/guide and https://bad.example.org/page.\n\n"
            "## References\n"
            "- https://docs.example.com/guide\n"
            "- https://bad.example.org/page\n"
        )
        sanitized, kept, found = eng_run._sanitize_references(
            md,
            ["HTTPS://DOCS.example.com"],
            no_external=False,
        )
        self.assertIn("https://docs.example.com/guide", sanitized)
        self.assertNotIn("bad.example.org", sanitized)
        self.assertEqual(kept, ["https://docs.example.com/guide"])
        self.assertIn("https://bad.example.org/page", found)

    def test_audit_references_detects_missing_links(self):
        failure = eng_run._audit_references(False, [], [])
        self.assertIsNotNone(failure)
        self.assertEqual(failure["reason"], "audit_failed_references")
        failure_filtered = eng_run._audit_references(False, ["https://bad"], [])
        self.assertEqual(failure_filtered["detail"], "all_urls_filtered")

    def test_duplicate_history_window(self):
        tmpdir = tempfile.mkdtemp()
        old_hist_path, old_hist_dir = eng_run.HIST_PATH, eng_run.HIST_DIR
        eng_run.HIST_DIR = tmpdir
        eng_run.HIST_PATH = os.path.join(tmpdir, "embeddings.jsonl")
        try:
            for i in range(60):
                eng_run.append_history({"slug": f"s{i}"})
            recents = eng_run.load_recent_history(50)
            self.assertEqual(len(recents), 50)
            self.assertEqual(recents[0]["slug"], "s10")
            self.assertEqual(recents[-1]["slug"], "s59")
        finally:
            eng_run.HIST_PATH = old_hist_path
            eng_run.HIST_DIR = old_hist_dir
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
