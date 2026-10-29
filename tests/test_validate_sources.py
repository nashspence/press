"""Regression tests for the source publication policy validator."""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_sources import validate_repository  # noqa: E402


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = Path("works/sample/manuscript.md")
        (self.root / self.path.parent).mkdir(parents=True)

    def check(self, text, additional=None):
        (self.root / self.path).write_bytes(text.encode("utf-8"))
        paths = [self.path]
        for rel, content in (additional or {}).items():
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            paths.append(Path(rel))
        return validate_repository(self.root, paths)

    def test_valid_unicode_math_anchors_and_internal_reference(self):
        source = (
            "# Structure and Identity\n\n"
            "<a id=\"sec-1\"></a>\n"
            "## § 1 — Foundations\n\n"
            "For every $x \u2208 S$, there is $y$ with $y=x$.\n\n"
            "$$\n\\forall x \\in S, \\quad x=x\n$$\n\n"
            "See [the section](#sec-1).\n"
        )
        self.assertEqual([], self.check(source))

    def test_non_nfc_rejected(self):
        source = "# Cafe\u0301\n"
        self.assertTrue(any("NFC" in e for e in self.check(source)))

    def test_missing_section_anchor_rejected(self):
        self.assertTrue(any("preceding" in e for e in self.check("# Title\n\n## Subsection\n")))

    def test_duplicate_anchor_rejected(self):
        source = "# Title\n\n<a id=\"same\"></a>\n## First\n\n<a id=\"same\"></a>\n## Second\n"
        self.assertTrue(any("duplicate explicit anchor" in e for e in self.check(source)))

    def test_broken_local_link_rejected(self):
        source = "# Title\n\n[missing source](does-not-exist.md)\n"
        self.assertTrue(any("broken local link" in e for e in self.check(source)))

    def test_broken_section_reference_rejected(self):
        source = "# Title\n\n[missing section](#no-such-id)\n"
        self.assertTrue(any("unresolved Markdown section link" in e for e in self.check(source)))

    def test_missing_image_alt_text_rejected(self):
        source = "# Title\n\n![](figure.svg)\n"
        (self.root / "works/sample/figure.svg").write_text("<svg/>", encoding="utf-8")
        self.assertTrue(any("alt text" in e for e in self.check(source)))

    def test_code_fence_does_not_require_an_anchor(self):
        source = "# Title\n\n```markdown\n## Example inside code\n```\n"
        self.assertEqual([], self.check(source))

    def test_inline_display_math_rejected(self):
        self.assertTrue(any("alone on its line" in e for e in self.check("# Title\n\nMath $$a+b$$.\n")))

    def test_unclosed_display_math_rejected(self):
        self.assertTrue(any("unclosed display-math" in e for e in self.check("# Title\n\n$$\nx + y\n")))

    def test_crlf_and_bom_rejected(self):
        raw = b"\xef\xbb\xbf# Title\r\n"
        (self.root / self.path).write_bytes(raw)
        errors = validate_repository(self.root, [self.path])
        self.assertTrue(any("BOM" in e for e in errors))
        self.assertTrue(any("LF line endings" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
