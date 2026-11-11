"""Testes do check_docs.py da skill codebase-agent-docs. Rodar com:
python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills/codebase-agent-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
from check_docs import check  # noqa: E402

INDEX = "[a](docs/agents/a.md)"


def lines(n: int, first: str = "x") -> str:
    return "\n".join([first] + ["x"] * (n - 1)) + "\n"


class CheckDocsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def make(self, files: dict[str, str]) -> Path:
        root = Path(self._tmp.name)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        return root

    def errors(self, files: dict[str, str]) -> list[str]:
        base = {"AGENTS.md": lines(10, INDEX), "docs/agents/a.md": lines(20)}
        return check(self.make({**base, **files}))

    def assertError(self, errs: list[str], *words: str):
        self.assertTrue(any(all(w in e for w in words) for e in errs), errs)

    def test_clean_set_passes(self):
        self.assertEqual(self.errors({}), [])

    def test_missing_root_is_error(self):
        self.assertError(check(self.make({"docs/agents/a.md": lines(20)})), "AGENTS.md")

    def test_root_over_120_lines_is_error(self):
        errs = self.errors({"AGENTS.md": lines(121, INDEX)})
        self.assertError(errs, "AGENTS.md", "120")

    def test_dir_guide_over_75_lines_is_error(self):
        errs = self.errors({"app/AGENTS.md": lines(76)})
        self.assertError(errs, "app/AGENTS.md", "75")

    def test_topic_over_140_lines_is_error(self):
        self.assertError(self.errors({"docs/agents/a.md": lines(141)}),
                         "docs/agents/a.md", "140")

    def test_topic_with_two_links_is_error(self):
        two = "[r](../../AGENTS.md) e [r](../../AGENTS.md)\n"
        errs = self.errors({"docs/agents/a.md": two})
        self.assertError(errs, "docs/agents/a.md", "link")

    def test_h3_outside_code_is_error(self):
        fenced = "```text\n### dentro\n```\n"
        self.assertEqual(self.errors({"docs/agents/a.md": fenced}), [])
        self.assertError(self.errors({"docs/agents/a.md": "### fora\n"}),
                         "docs/agents/a.md", "###")

    def test_broken_relative_link_is_error(self):
        root = INDEX + " [b](docs/agents/sumiu.md)"
        errs = self.errors({"AGENTS.md": root})
        self.assertError(errs, "AGENTS.md", "docs/agents/sumiu.md")

    def test_topic_not_in_root_index_is_error(self):
        self.assertError(self.errors({"docs/agents/b.md": lines(5)}),
                         "docs/agents/b.md", "índice")

    def test_cited_path_that_does_not_exist_is_error(self):
        topic = "Veja `app/velho.py`.\n"
        errs = self.errors({"app/a.py": "1\n", "docs/agents/a.md": topic})
        self.assertError(errs, "docs/agents/a.md", "app/velho.py")

    def test_cited_line_beyond_file_is_error(self):
        topic = "`app/a.py:2` e `app/a.py:9`\n"
        files = {"app/a.py": "1\n2\n3\n", "docs/agents/a.md": topic}
        errs = self.errors(files)
        self.assertError(errs, "app/a.py:9")
        self.assertFalse(any("app/a.py:2" in e for e in errs), errs)

    def test_dir_guide_cites_relative_to_its_folder(self):
        files = {"tests/t.py": "1\n", "app/tests/test_x.py": "1\n",
                 "app/AGENTS.md": "`tests/test_x.py` checa isso.\n"}
        self.assertEqual(self.errors(files), [])

    def test_ignores_placeholders_and_commands(self):
        text = ("`<name>/x.py` `make run` `src/x.py` `https://x.io/a` `*.md` `app.text`"
                " `/docs` `/health/live` `/connect/...`\n")
        self.assertEqual(self.errors({"app/a.py": "1\n", "docs/agents/a.md": text}), [])


if __name__ == "__main__":
    unittest.main()
