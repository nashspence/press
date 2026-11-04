"""Documentation is not a second executable-command interface."""
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def test_help_is_complete_and_is_make_default(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        phony = set(re.findall(r"(?m)^\.PHONY:\s*(.*?)\s*$", makefile)[0].split())
        definitions = re.findall(r"(?m)^([a-z][a-z0-9-]*):[^\n]*?(?:\s+##\s*(.*))?$", makefile)
        names = [name for name, _ in definitions]
        self.assertEqual(len(names), len(set(names)), "duplicate public Make targets")
        self.assertEqual(phony, set(names), "all targets must be phony and documented")
        for name, description in definitions:
            self.assertTrue(description, f"{name} requires an inline help description")

        help_result = subprocess.check_output(["make", "help"], cwd=ROOT, text=True)
        self.assertEqual(help_result, subprocess.check_output(["make"], cwd=ROOT, text=True))
        displayed = re.findall(r"(?m)^  ([a-z][a-z0-9-]*)\s{2,}(\S.*)$", help_result)
        self.assertEqual(dict(definitions), dict(displayed))

        for name, description in definitions:
            recipe = makefile.split(f"\n{name}:", 1)[1].split("\n\n", 1)[0]
            for required in re.findall(r"\$\$\{([A-Z_]+):\?", recipe):
                self.assertIn(required + "=", description, f"{name} must describe {required}")

    def test_prose_does_not_document_a_competing_cli(self):
        # The Makefile is the only supported command reference; prose points to help.
        for file in ROOT.glob("*.md"):
            source = file.read_text(encoding="utf-8")
            with self.subTest(file=file.name):
                self.assertNotRegex(source, r"(?m)^```(?:sh|shell|bash|console|terminal)\b")
                self.assertNotRegex(source, r"`make\s+(?!help`)[a-z][a-z0-9-]*`")
                self.assertNotRegex(source, r"`mise\s+(?:x|exec|run|install)\b")


if __name__ == "__main__":
    unittest.main()
