from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / "permissions"))
import gh_api_guard as g  # noqa: E402

ASK = [
    "gh api graphql -f query='query A { viewer { id } } mutation B { x }'",
    "gh api repos/o/r/x \\\n  -X POST",
    "cat > f <<'EOF'\ntexto\nEOF\ngh api repos/o/r/x -f a=b",
    "gh api repos/o/r/issues -f title=x",
    "gh api repos/o/r/issues -F body=@f",
    "gh api repos/o/r/issues --field a=b",
    "gh api repos/o/r/issues --raw-field a=b",
    "gh api -X DELETE repos/o/r/issues/1",
    "gh api -XPOST repos/o/r/issues",
    "gh api --method PATCH repos/o/r/pulls/1",
    "gh api --method=PUT repos/o/r/x",
    "gh api repos/o/r/x --input body.json",
    "cd /tmp && gh api repos/o/r/x -f a=b | jq .",
    "echo ok; gh api repos/o/r/x -X POST",
    "gh api graphql -f query='mutation { addComment(input:{}) { id } }'",
    "gh api graphql -f query=@q.graphql",
    "gh api graphql -f query=\"$Q\"",
    "gh api graphql",
]
ALLOW = [
    "gh api graphql -F owner=o -f query='\nquery($o:String!){repository(owner:$o){id}}' \\\n  --jq '.data'",
    "cat > f.md <<'EOF'\nuse gh api repos/o/r -f a=b\nEOF\ngh api repos/o/r/pulls/1",
    "gh api repos/o/r/pulls/1",
    "gh api repos/o/r/pulls/1 --jq '.title'",
    "gh api -X GET repos/o/r/pulls",
    "gh api --method GET repos/o/r/pulls --paginate",
    "gh api repos/o/r/pulls -H 'Accept: application/json' -q '.[]'",
    "cd /tmp && gh api repos/o/r/x | jq .",
    "gh pr view 1",
    "echo 'gh api -f x'",
    "git log --grep='gh api -X POST'",
    "gh api graphql -F owner=o -F n=1 -f query='query($n:Int!){repository(name:\"r\"){id}}'",
    "gh api graphql -f query='query { viewer { login } }' --jq .data",
]


class VerdictTest(unittest.TestCase):
    def test_writes_ask(self):
        for cmd in ASK:
            self.assertIsNotNone(g.verdict(cmd), cmd)

    def test_reads_pass(self):
        for cmd in ALLOW:
            self.assertIsNone(g.verdict(cmd), cmd)

    def test_malformed_quoting_asks_when_gh_api_present(self):
        self.assertIsNotNone(g.verdict("gh api repos/o/r/x -f 'a=b"))


class MainTest(unittest.TestCase):
    def run_hook(self, command: str) -> str:
        out = io.StringIO()
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(out):
            code = g.main()
        self.assertEqual(code, 0)
        return out.getvalue()

    def test_write_emits_ask_decision(self):
        data = json.loads(self.run_hook("gh api repos/o/r/x -X DELETE"))
        spec = data["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertEqual(spec["permissionDecision"], "ask")
        self.assertTrue(spec["permissionDecisionReason"])

    def test_read_emits_nothing(self):
        self.assertEqual(self.run_hook("gh api repos/o/r/pulls/1"), "")

    def test_garbage_stdin_emits_nothing(self):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("não é json")), redirect_stdout(out):
            self.assertEqual(g.main(), 0)
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
