"""Positive/negative executable tests for Press source format v1."""

import yaml
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_sources import validate_repository  # noqa: E402


MANUSCRIPT = ("# On Structure and Identity\n\n"
              "<a id=\"sec-1\"></a>\n## § 1 — Foundations\n\n"
              "Let $S$ denote symbols, and consider $x \\in S$.\n\n"
              "$$\n\\forall x \\in S, \\quad x=x\n$$\n\n"
              "See [the section](#sec-1).\n")
METADATA = {
    "author": "nashspence", "language": "en", "rights": "all-rights-reserved",
    "schema": "press.work.v1", "slug": "sample", "status": "draft",
    "title": "On Structure and Identity"
}


class StrictSourceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = Path("works/sample/manuscript.md")
        (self.root / self.source.parent).mkdir(parents=True)

    def check(self, source=MANUSCRIPT, metadata=METADATA, other=None, front_matter=None):
        if front_matter is not None:
            prefix = front_matter
        elif metadata is None:
            prefix = ""
        else:
            prefix = "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n\n"
        (self.root / self.source).write_bytes((prefix + source).encode("utf-8"))
        paths = [self.source]
        for name, content in (other or {}).items():
            path = Path(name)
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
            paths.append(path)
        return validate_repository(self.root, paths)

    def assert_bad(self, needle, source=MANUSCRIPT, metadata=METADATA, other=None):
        errors = self.check(source, metadata, other)
        self.assertTrue(any(needle in error for error in errors), "expected " + needle + "; got " + str(errors))

    def test_canonical_example(self):
        self.assertEqual([], self.check())

    def test_plain_document_without_yaml_renders(self):
        self.check()
        notes = Path("notes.md")
        (self.root / notes).write_text("# Notes\n\nOrdinary Markdown.\n", encoding="utf-8")
        self.assertEqual([], validate_repository(self.root, [self.source, notes]))

    def test_notes_and_gfm_table(self):
        content = MANUSCRIPT + "A note[^ref].\n\n[^ref]: Context.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
        self.assertEqual([], self.check(content))

    def test_invalid_utf8(self):
        self.check()
        (self.root / self.source).write_bytes(b"\xff# Title\n")
        self.assertIn("UTF-8", " ".join(validate_repository(self.root, [self.source])))

    def test_bom(self):
        front = "\ufeff---\n" + yaml.safe_dump(METADATA, sort_keys=False) + "---\n\n"
        self.assertTrue(any("BOM" in e for e in self.check(front_matter=front)))

    def test_nfc(self):
        self.assert_bad("NFC", MANUSCRIPT.replace("Identity", "Identite\u0301"))

    def test_bidi_override_prohibited(self):
        self.assert_bad("bidirectional override", MANUSCRIPT + "Suspicious \u202e reversal.\n")

    def test_unknown_work_source_file(self):
        self.assert_bad("unsupported file path", other={"works/sample/random.txt": "unvalidated material\n"})

    def test_crlf(self):
        self.assert_bad("CR/CRLF", MANUSCRIPT.replace("\n", "\r\n"))

    def test_final_newline(self):
        self.assert_bad("final newline", MANUSCRIPT.rstrip("\n"))

    def test_trailing_whitespace(self):
        self.assert_bad("trailing whitespace", MANUSCRIPT.replace("## § 1 — Foundations\n", "## § 1 — Foundations \n"))

    def test_no_h1(self):
        self.assert_bad("exactly one ATX H1", MANUSCRIPT.replace("# On Structure", "## On Structure"))

    def test_duplicate_h1(self):
        self.assert_bad("exactly one ATX H1", MANUSCRIPT + "\n# Another title\n")

    def test_skip_heading_level(self):
        self.assert_bad("heading level skipped", MANUSCRIPT.replace("## § 1", "#### § 1"))

    def test_missing_anchor(self):
        self.assert_bad("requires an explicit stable anchor", MANUSCRIPT.replace('<a id="sec-1"></a>\n', ""))

    def test_orphan_anchor(self):
        self.assert_bad("unattached anchor", MANUSCRIPT + '\n<a id="orphan"></a>\n')

    def test_duplicate_anchor(self):
        self.assert_bad("duplicate anchor", MANUSCRIPT.replace('<a id="sec-1"></a>', '<a id="sec-1"></a>\n<a id="sec-1"></a>'))

    def test_reject_arbitrary_html(self):
        self.assert_bad("raw HTML is prohibited", MANUSCRIPT + "<script>alert(1)</script>\n")

    def test_reject_legacy_math(self):
        self.assert_bad("not backslash math delimiters", MANUSCRIPT + r"\(x\)" + "\n")

    def test_unbalanced_inline_math(self):
        self.assert_bad("unmatched inline $", MANUSCRIPT + "An $unclosed dollar.\n")

    def test_math_not_parsed(self):
        self.assert_bad("math delimiters did not parse", MANUSCRIPT + "This is $ x $ with spaces.\n")

    def test_currency_must_be_escaped(self):
        self.assert_bad("unmatched inline $", MANUSCRIPT + "Cost is $5.\n")

    def test_escaped_currency(self):
        self.assertEqual([], self.check(MANUSCRIPT + r"Cost is \$5." + "\n"))

    def test_inline_double_dollar(self):
        self.assert_bad("display math $$ must be alone", MANUSCRIPT + "$$E=mc^2$$\n")

    def test_unclosed_display_math(self):
        self.assert_bad("unclosed display math", MANUSCRIPT + "$$\nE=mc^2\n")

    def test_unmatched_code_span(self):
        self.assert_bad("unmatched backtick", MANUSCRIPT + "An `unclosed code span.\n")

    def test_code_fence_masks_headings_and_math(self):
        self.assertEqual([], self.check(MANUSCRIPT + "```markdown\n## Hidden heading\n$$ignored$$\n```\n"))

    def test_unclosed_fence(self):
        self.assert_bad("unclosed fenced code", MANUSCRIPT + "```md\nexample\n")

    def test_footnote_ref_missing_definition(self):
        self.assert_bad("unresolved footnote", MANUSCRIPT + "A missing[^note].\n")

    def test_footnote_unused_definition(self):
        self.assert_bad("unused footnote", MANUSCRIPT + "[^unused]: Unused.\n")

    def test_footnote_duplicate_definition(self):
        self.assert_bad("duplicate footnote", MANUSCRIPT + "A note[^x].\n\n[^x]: One.\n[^x]: Two.\n")

    def test_local_link_broken(self):
        self.assert_bad("broken local link", MANUSCRIPT + "[missing](missing.md)\n")

    def test_local_link_untracked(self):
        dest = self.root / "works/sample/untracked.md"
        dest.write_text("# Local\n", encoding="utf-8")
        self.assert_bad("linked file is not tracked", MANUSCRIPT + "[untracked](untracked.md)\n")

    def test_local_fragment_missing(self):
        self.assert_bad("unresolved Markdown section link", MANUSCRIPT + "[wrong](#missing)\n")

    def test_reject_insecure_url(self):
        self.assert_bad("unsupported/external URI", MANUSCRIPT + "[bad](javascript:alert(1))\n")

    def test_reject_image_missing_alt(self):
        self.assert_bad("image alt text required", MANUSCRIPT + "![](assets/sample.svg)\n",
                        other={"works/sample/assets/sample.svg": '<svg xmlns="http://www.w3.org/2000/svg"/>\n'})

    def test_reject_external_image(self):
        self.assert_bad("unsupported/external URI", MANUSCRIPT + "![pic](https://example.com/image.png)\n")

    def test_valid_svg_asset(self):
        source = MANUSCRIPT + "![plot](assets/figure.svg)\n"
        other = {"works/sample/assets/figure.svg": '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>\n'}
        self.assertEqual([], self.check(source, other=other))

    def test_reject_executable_svg(self):
        source = MANUSCRIPT + "![plot](assets/figure.svg)\n"
        other = {"works/sample/assets/figure.svg": '<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>\n'}
        self.assert_bad("SVG element", source, other=other)

    def test_requires_metadata(self):
        self.assert_bad("requires YAML front matter", metadata=None)

    def test_metadata_schema(self):
        self.assert_bad("schema keys mismatch", metadata={**METADATA, "extra": "unexpected"})

    def test_metadata_title_mismatch(self):
        self.assert_bad("title must exactly match", metadata={**METADATA, "title": "Incorrect"})

    def test_metadata_slug_mismatch(self):
        self.assert_bad("slug must match", metadata={**METADATA, "slug": "other"})

    def test_metadata_invalid_rights(self):
        self.assert_bad("enumerated rights", metadata={**METADATA, "rights": "MIT"})

    def test_metadata_published_status_disallowed(self):
        self.assert_bad("status must remain draft", metadata={**METADATA, "status": "published"})

    def test_does_not_validate_heading_inside_code(self):
        content = MANUSCRIPT + '````\n<a id="fake"></a>\n## Not a section\n````\n'
        self.assertEqual([], self.check(content))

    def test_yaml_duplicate_key(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False) + "title: Duplicate\n---\n\n"
        self.assertTrue(any("duplicate YAML key" in e for e in self.check(front_matter=front)))

    def test_yaml_custom_tag(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "title: On Structure and Identity", "title: !my-tag On Structure and Identity") + "---\n\n"
        self.assertTrue(any("prohibited" in e for e in self.check(front_matter=front)))

    def test_yaml_alias_and_anchor(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "author: nashspence", "author: &alias nashspence").replace(
            "title: On Structure and Identity", "title: *alias") + "---\n\n"
        self.assertTrue(any("prohibited" in e for e in self.check(front_matter=front)))

    def test_yaml_merge_key(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False) + "<<: *not-defined\n---\n\n"
        self.assertTrue(any("prohibited" in e or "invalid YAML" in e for e in self.check(front_matter=front)))

    def test_yaml_list_type(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "author: nashspence", "author: [Nash, Spence]") + "---\n\n"
        self.assertTrue(any("string scalar" in e for e in self.check(front_matter=front)))

    def test_yaml_boolean_must_be_quoted(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "author: nashspence", "author: yes") + "---\n\n"
        self.assertTrue(any("quote ambiguous" in e for e in self.check(front_matter=front)))

    def test_yaml_numbers_must_be_quoted(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "author: nashspence", "author: 2026") + "---\n\n"
        self.assertTrue(any("quote ambiguous" in e for e in self.check(front_matter=front)))

    def test_yaml_unknown_key(self):
        self.assert_bad("schema keys mismatch", metadata={**METADATA, "date": "2026-10-29"})

    def test_yaml_missing_key(self):
        self.assert_bad("schema keys mismatch", metadata={k:v for k,v in METADATA.items() if k!="author"})

    def test_yaml_multiline_scalar(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "title: On Structure and Identity", "title: |\n  On Structure and Identity") + "---\n\n"
        self.assertTrue(any("multiline" in e or "flat single-line" in e for e in self.check(front_matter=front)))

    def test_yaml_invalid_syntax(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "author: nashspence", "author: [") + "---\n\n"
        self.assertTrue(any("invalid YAML" in e for e in self.check(front_matter=front)))

    def test_unclosed_front_matter(self):
        self.assertTrue(any("missing closing" in e for e in self.check(front_matter="---\nschema: press.work.v1\n")))

    def test_front_matter_requires_blank_separator(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False) + "---\n"
        self.assertTrue(any("blank line" in e for e in self.check(front_matter=front)))

    def test_front_matter_rejects_extra_blank_separator(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False) + "---\n\n\n"
        self.assertTrue(any("exactly one blank line" in e for e in self.check(front_matter=front)))

    def test_yaml_quotes_colon_and_comment(self):
        title = "On Structure: Identity"
        front = "---\n" + yaml.safe_dump({**METADATA, "title": title}, sort_keys=False)
        front += "# This is an author comment.\n---\n\n"
        body = MANUSCRIPT.replace("On Structure and Identity", title)
        self.assertEqual([], self.check(body, front_matter=front))

    def test_yaml_metadata_with_markdown_interpretation_disallowed(self):
        front = "---\n" + yaml.safe_dump(METADATA, sort_keys=False).replace(
            "author: nashspence", 'author: "*nashspence*"') + "---\n\n"
        self.assertTrue(any("Pandoc metadata differs" in e for e in self.check(front_matter=front)))

    def test_old_json_metadata_not_allowed(self):
        self.assert_bad("unsupported file path", other={"works/sample/metadata.json": "{}\n"})

    def test_work_directory_requires_manuscript(self):
        (self.root / self.source.parent / "README.md").write_text("# Notes\n", encoding="utf-8")
        errors = validate_repository(self.root, [Path("works/sample/README.md")])
        self.assertTrue(any("requires manuscript.md" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
