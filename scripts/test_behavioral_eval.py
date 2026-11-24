"""Offline regression tests for evaluation execution boundaries."""
import argparse
import contextlib
import io
import json
import subprocess
import sys
import unittest
from unittest import mock

import run_behavioral_eval as harness


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.case = {"id": "fixture", "prompt": "a harmless request", "authorization": "none", "expected_route": "direct"}

    def test_default_is_dry_and_calls_nothing(self):
        with mock.patch.object(sys, "argv", ["eval"]), mock.patch.object(harness, "run_case") as run, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(harness.main(), 0)
        run.assert_not_called()
        self.assertIn("no commands or models called", output.getvalue())

    def test_no_implicit_live_call(self):
        with mock.patch.object(harness, "run_codex") as live:
            with self.assertRaises(ValueError):
                harness.run_case(self.case, None, None)
        live.assert_not_called()

    def test_prompt_remains_data_over_stdin(self):
        self.case["prompt"] = "$(touch /tmp/flightdeck-must-not-exist) `echo unsafe` ; \"quoted\"\nnext line"
        # The child echoes its input; a shell would interpret these metacharacters.
        argv = [sys.executable, "-c", "import sys; print(sys.stdin.read())"]
        actual = json.loads(harness.run_case(self.case, None, argv))
        self.assertEqual(actual["case"]["prompt"], self.case["prompt"])
        self.assertIn("plan-only", actual["prompt"])

    def test_nonzero_runner_is_failure(self):
        with self.assertRaises(subprocess.CalledProcessError):
            harness.run_case(self.case, None, [sys.executable, "-c", "raise SystemExit(2)"])

    def test_timeout_is_bounded(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            harness.run_case(self.case, None, [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05)

    def test_route_requires_complete_single_line(self):
        for route in ("direct", "decision", "batch", "stop"):
            self.assertEqual(harness.extract_route("route: " + route + "\n"), route)
        for output in ("route: sol", "explanation route: direct", "route: direct\nroute: stop", "route: direct please"):
            self.assertIsNone(harness.extract_route(output))

    def test_runner_argv_validates_structure(self):
        self.assertEqual(harness.runner_argv('["python3", "fixture.py"]'), ["python3", "fixture.py"])
        for value in ('"echo route: direct"', '[]', '[1]', '[""]', 'not json'):
            with self.assertRaises(argparse.ArgumentTypeError):
                harness.runner_argv(value)

    def test_live_uses_explicit_arguments_and_stdin(self):
        with mock.patch.object(harness.subprocess, "run") as run, mock.patch.object(harness.Path, "read_text", return_value="route: direct"):
            self.assertEqual(harness.run_case(self.case, "verified-runtime-id", None, live=True), "route: direct")
        positional, options = run.call_args
        self.assertIn("verified-runtime-id", positional[0])
        self.assertEqual(positional[0][-1], "-")
        self.assertIn("plan-only", options["input"])
        self.assertNotIn("shell", options)

    def test_model_without_live_is_rejected(self):
        with mock.patch.object(sys, "argv", ["eval", "--model", "invented"]), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                harness.main()
        self.assertEqual(result.exception.code, 2)

    def test_fixture_routes_use_decision(self):
        cases = harness.load_cases()
        self.assertGreaterEqual(len(cases), 20)
        self.assertNotIn("sol", {case["expected_route"] for case in cases})
        self.assertIn("quorum-missing-reviewer", {case["id"] for case in cases})


if __name__ == "__main__":
    unittest.main()
