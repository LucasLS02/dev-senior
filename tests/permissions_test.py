"""Testes das listas de permissão e da mescla nos arquivos de cada ferramenta.
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "permissions"))
import apply  # noqa: E402
import rules  # noqa: E402

HOOK = "python3 /x/gh_api_guard.py"


class RulesTest(unittest.TestCase):
    def test_tracker_writes_require_approval(self):
        for cmd in ("gh issue create", "gh issue edit", "gh issue comment",
                    "acli jira workitem create", "acli jira workitem edit",
                    "acli jira workitem transition", "az boards work-item create",
                    "az boards work-item update", "az boards work-item relation add"):
            self.assertIn(cmd, rules.ASK)

    def test_nothing_destructive_is_allowed(self):
        for cmd in rules.ALL:
            for bad in rules.NEVER_ALLOW:
                self.assertFalse(cmd == bad or cmd.startswith(bad + " "), cmd)

    def test_ask_list_has_no_overlap_with_allow(self):
        self.assertEqual(set(rules.ALL) & set(rules.ASK), set())

    def test_pnpm_exec_is_open_only_for_checkers(self):
        execs = [c for c in rules.ALL if c.startswith("pnpm exec")]
        self.assertIn("pnpm exec tsc", execs)
        self.assertNotIn("pnpm exec", rules.ALL)
        self.assertIn("pnpm exec biome", execs)
        self.assertTrue(all(c.split()[2] in rules.JS_CHECKERS for c in execs))

    def test_npx_and_node_are_open_only_for_checkers_and_tests(self):
        npx = [c for c in rules.ALL if c.startswith("npx")]
        self.assertIn("npx biome ci", npx)
        self.assertIn("npx tsc", npx)
        self.assertIn("npx next build", npx)
        self.assertTrue(all(c.split()[1] in (*rules.JS_CHECKERS, "next") for c in npx))
        self.assertIn("node --experimental-strip-types --test", rules.ALL)
        for open_ended in ("npx", "node", "env", "pnpm exec"):
            self.assertNotIn(open_ended, rules.ALL)

    def test_pnpm_validation_scripts_are_open_but_install_and_mock_are_not(self):
        for cmd in ("pnpm lint:ci", "pnpm e2e", "pnpm e2e:i18n-contract", "pnpm test:components",
                    "pnpm deploy:validate", "pnpm audit", "pnpm playwright test", "pnpm tsc"):
            self.assertIn(cmd, rules.ALL)
        for cmd in ("pnpm install", "pnpm add", "pnpm mock", "pnpm exec", "pnpm"):
            self.assertNotIn(cmd, rules.ALL)

    def test_make_is_never_open(self):
        self.assertNotIn("make", rules.ALL)
        self.assertTrue(all(c.startswith("make ") for c in rules.ALL if c.startswith("make")))


class ClaudeTest(unittest.TestCase):
    def test_merge_keeps_existing_and_is_idempotent(self):
        base = {"model": "x", "permissions": {"defaultMode": "auto", "allow": ["Bash(brew list:*)"]}}
        once = apply.merge_claude(base, HOOK)
        self.assertEqual(once["model"], "x")
        self.assertEqual(once["permissions"]["defaultMode"], "auto")
        self.assertIn("Bash(brew list:*)", once["permissions"]["allow"])
        self.assertIn("Bash(git status:*)", once["permissions"]["allow"])
        self.assertEqual(apply.merge_claude(once, HOOK), once)
        self.assertEqual(base["permissions"]["allow"], ["Bash(brew list:*)"])  # entrada intacta

    def test_hook_is_added_once_next_to_existing_hooks(self):
        other = {"matcher": "Edit", "hooks": [{"type": "command", "command": "fmt"}]}
        base = {"hooks": {"PreToolUse": [other], "Stop": [{"hooks": []}]}}
        merged = apply.merge_claude(apply.merge_claude(base, HOOK), HOOK)
        pre = merged["hooks"]["PreToolUse"]
        self.assertEqual(pre[0], other)
        self.assertEqual(sum(HOOK in json.dumps(e) for e in pre), 1)
        self.assertIn("Stop", merged["hooks"])


class SecretsTest(unittest.TestCase):
    def test_claude_denies_credentials_and_asks_for_env(self):
        perms = apply.merge_claude({}, HOOK)["permissions"]
        self.assertIn("Read(~/.ssh/**)", perms["deny"])
        self.assertIn("Read(**/*.pem)", perms["deny"])
        self.assertIn("Bash(cat ~/.ssh:*)", perms["deny"])
        self.assertIn(f"Bash(grep {Path.home()}/.aws:*)", perms["deny"])
        self.assertIn("Read(**/.env)", perms["ask"])
        self.assertIn("Bash(cat .env:*)", perms["ask"])
        self.assertEqual(apply.merge_claude(apply.merge_claude({}, HOOK), HOOK)["permissions"], perms)

    def test_nothing_denied_is_also_allowed(self):
        perms = apply.merge_claude({}, HOOK)["permissions"]
        self.assertEqual(set(perms["deny"]) & set(perms["allow"]), set())
        self.assertEqual(set(perms["ask"]) & set(perms["allow"]), set())

    def test_antigravity_denies_credentials_by_regex(self):
        perms = apply.merge_antigravity({})["permissions"]
        self.assertTrue(any(".ssh" in d and d.startswith("command(regex:") for d in perms["deny"]))
        self.assertTrue(any(".env" in a and a.startswith("command(regex:") for a in perms["ask"]))

    def test_opencode_denies_readers_on_credential_dirs_after_the_allows(self):
        out = apply.merge_opencode(OpencodeTest.TEXT)
        self.assertIn('"cat *.ssh*": "deny"', out)
        self.assertLess(out.index('"cat *": "allow"'), out.index('"cat *.ssh*": "deny"'))


class AntigravityTest(unittest.TestCase):
    def test_merge_adds_allow_and_gh_api_write_ask(self):
        merged = apply.merge_antigravity({"model": "m", "permissions": {"deny": ["command(sudo)"]}})
        perms = merged["permissions"]
        self.assertIn("command(sudo)", perms["deny"])
        self.assertIn("command(git status)", perms["allow"])
        self.assertIn("command(gh api)", perms["allow"])
        self.assertTrue(any(a.startswith("command(regex:gh api") for a in perms["ask"]))
        self.assertEqual(apply.merge_antigravity(merged), merged)


class OpencodeTest(unittest.TestCase):
    TEXT = ('{\n  "permission": {\n    "bash": {\n      "*": "ask",\n'
            '      "ls *": "allow",\n      "rm *": "deny"\n    }\n  }\n}\n')

    def test_block_goes_before_rm_and_result_is_valid_jsonc(self):
        out = apply.merge_opencode(self.TEXT)
        self.assertLess(out.index("dev-senior:begin"), out.index('"rm *": "deny"'))
        data = json.loads("\n".join(
            line for line in out.splitlines() if not line.strip().startswith("//")))
        bash = data["permission"]["bash"]
        self.assertEqual(bash["git status *"], "allow")
        self.assertEqual(bash["git status"], "allow")
        self.assertEqual(bash["git push *"], "ask")
        self.assertEqual(bash["gh api * -X *"], "ask")
        self.assertEqual(bash["rm *"], "deny")
        self.assertNotIn("rm", [k for k, v in bash.items() if v == "ask"])

    def test_rerun_replaces_the_block_instead_of_duplicating(self):
        once = apply.merge_opencode(self.TEXT)
        self.assertEqual(apply.merge_opencode(once), once)

    def test_missing_anchor_is_an_error(self):
        with self.assertRaises(ValueError):
            apply.merge_opencode('{"permission": {"bash": {"*": "ask"}}}')


class CodexTest(unittest.TestCase):
    def test_rules_text(self):
        text = apply.codex_rules()
        self.assertIn('prefix_rule(pattern=["git", "status"], decision="allow")', text)
        self.assertIn('prefix_rule(pattern=["gh", "api"], decision="prompt")', text)
        self.assertNotIn('"rm"', text)


if __name__ == "__main__":
    unittest.main()
