"""Regression tests for PAIDEIA-Hermes. Stdlib only — no pytest, no fixtures.

    python3 -m unittest discover -s tests -v      (from the repo root)
    ./tests/run.sh

The plugin is loaded the way hermes loads it (as the package
``hermes_plugins.paideia``) so the ``from . import …`` relative imports resolve.

Two kinds of test live here:

* **Behaviour** — the bugs fixed in 0.4.0, each pinned so it can't come back.
* **Contract** — invariants that span files and would otherwise drift silently:
  ``pd_doctor`` deliberately keeps its own copies of SKELETON/META_KEYS/the
  payload list so it can run standalone, and every LLM subcommand needs a spec
  file and a skill that actually exists on disk. Duplication is fine as long as
  something checks it.
"""
from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import os
import random
import shutil
import string
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load_plugin() -> types.ModuleType:
    """Import the checkout as ``hermes_plugins.paideia``, running its __init__.

    This mirrors how hermes' PluginManager loads it from
    ``~/.hermes/plugins/paideia/``, so the ``from . import …`` relative imports
    and ``register()`` behave exactly as they do in production — without needing
    the checkout to physically live under a ``hermes_plugins/`` directory.
    """
    if "hermes_plugins" not in sys.modules:
        parent = types.ModuleType("hermes_plugins")
        parent.__path__ = []
        sys.modules["hermes_plugins"] = parent

    spec = importlib.util.spec_from_file_location(
        "hermes_plugins.paideia",
        REPO / "__init__.py",
        submodule_search_locations=[str(REPO)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["hermes_plugins.paideia"] = module
    spec.loader.exec_module(module)
    return module


PLUGIN = _load_plugin()
pd_commands = importlib.import_module("hermes_plugins.paideia.pd_commands")
pd_doctor = importlib.import_module("hermes_plugins.paideia.pd_doctor")
pd_errlog = importlib.import_module("hermes_plugins.paideia.pd_errlog")
pd_meta = importlib.import_module("hermes_plugins.paideia.pd_meta")
pd_prompts = importlib.import_module("hermes_plugins.paideia.pd_prompts")
pd_status = importlib.import_module("hermes_plugins.paideia.pd_status")
pd_weakmap = importlib.import_module("hermes_plugins.paideia.pd_weakmap")
pd_workspace = importlib.import_module("hermes_plugins.paideia.pd_workspace")

pd_render = importlib.import_module("pd_render") if str(REPO) in sys.path else None
if pd_render is None:
    sys.path.insert(0, str(REPO))
    pd_render = importlib.import_module("pd_render")
pd_vision_ocr = importlib.import_module("pd_vision_ocr")


class TempCourse(unittest.TestCase):
    """Base class giving each test its own scratch course folder."""

    #: Overridden by the glob-metacharacter test.
    folder_name = "course"

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="paideia-test-")
        self.cwd = Path(self._tmp) / self.folder_name
        self.cwd.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def scaffold(self, **overrides: str) -> dict[str, str]:
        meta = {
            "COURSE_NAME": "Complex Analysis",
            "EXAM_DATE": "2099-01-01",
            "EXAM_TYPE": "final",
            "USER_WEAK_ZONES": "unknown",
            "OCR_ENGINE": "claude",
            "INTERFACE_LANG": "en",
        }
        meta.update(overrides)
        pd_workspace.scaffold_course(self.cwd, meta)
        return meta


class TestErrorLogYAML(TempCourse):
    """errors/log.md is the one file every weakness surface parses."""

    def _entries(self) -> list[dict]:
        yaml = _require_yaml()
        text = pd_errlog.read_errors(self.cwd)
        # Strip the seed's schema comment; what remains must be a YAML document.
        body = text.split("-->", 1)[1] if "-->" in text else text
        return yaml.safe_load(body) or []

    def test_latex_summary_stays_parseable(self) -> None:
        """A summary full of LaTeX must not break the whole log.

        Regression: backslashes went into a double-quoted scalar unescaped, so
        `\\int` read as the unknown escape `\\i` and YAML rejected the file.
        """
        pd_errlog.append_error(
            self.cwd,
            problem_id="q1",
            pattern="P3",
            error_type="sign",
            summary=r"missed \int by parts; used \frac{1}{2} and \\ wrongly",
            source="answers/converted/q1.md",
        )
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["summary"],
            r"missed \int by parts; used \frac{1}{2} and \\ wrongly",
        )

    def test_hostile_values_stay_parseable(self) -> None:
        """Quotes, colons, hashes and newlines must not end a scalar early."""
        pd_errlog.append_error(
            self.cwd,
            problem_id='q2: "weird" #1',
            pattern="P7",
            error_type="pattern-missed",
            summary='he said "use $x: y$"\nthen stopped # here',
            source="answers/converted/q2.md",
        )
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertIn("weird", str(entries[0]["problem_id"]))
        self.assertIn("stopped", entries[0]["summary"])

    def test_pattern_key_stays_unquoted(self) -> None:
        """PATTERN_RX matches `pattern: P3` — quoting it would hide the entry."""
        pd_errlog.append_error(
            self.cwd, problem_id="q3", pattern="P9", error_type="algebraic",
            summary=r"\alpha", source="s.md",
        )
        text = pd_errlog.read_errors(self.cwd)
        self.assertIn("\n  pattern: P9\n", text)
        self.assertEqual(pd_errlog.pattern_counts(text).get("P9"), 1)
        self.assertEqual(pd_errlog.top_pattern(self.cwd), "P9")

    def test_multiple_appends_accumulate(self) -> None:
        for i in range(3):
            pd_errlog.append_error(
                self.cwd, problem_id=f"q{i}", pattern="P1", error_type="sign",
                summary=r"\sigma sign flip", source="s.md",
            )
        self.assertEqual(len(self._entries()), 3)
        self.assertEqual(pd_errlog.pattern_counts(pd_errlog.read_errors(self.cwd)), {"P1": 3})


class TestFuzz(TempCourse):
    """Seeded fuzz over the three surfaces that take arbitrary user text.

    Course names, error summaries and problem IDs are free-form and routinely
    carry LaTeX, CJK and emoji. These assert the invariants hold across that
    whole space, not just the handful of cases the targeted tests name.
    """

    ALPHABET = string.printable + "한글수식∫∑🔥🟡⚪"
    N = 120

    def _rand(self, rng, n: int) -> str:
        return "".join(rng.choice(self.ALPHABET) for _ in range(rng.randint(0, n)))

    def test_dispatch_never_raises_on_arbitrary_input(self) -> None:
        rng = random.Random(7)
        cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            for _ in range(self.N):
                raw = self._rand(rng, 60)
                self.assertIsInstance(pd_commands.dispatch(raw), str, repr(raw))
        finally:
            os.chdir(cwd)

    def test_error_log_stays_valid_yaml_under_fuzz(self) -> None:
        yaml = _require_yaml()
        for seed in range(8):          # several seeds: one corpus misses too much
            course = self.cwd / f"c{seed}"
            course.mkdir()
            rng = random.Random(seed)
            for i in range(self.N // 4):
                pd_errlog.append_error(
                    course,
                    problem_id=self._rand(rng, 20) or "x",
                    pattern=f"P{i % 9 + 1}",
                    error_type=rng.choice(pd_errlog.ERROR_TYPES),
                    summary=self._rand(rng, 120),
                    source=self._rand(rng, 40) or "s.md",
                )
            text = pd_errlog.read_errors(course)
            entries = yaml.safe_load(text.split("-->", 1)[1])
            self.assertEqual(len(entries), self.N // 4,
                             f"seed {seed}: an entry was swallowed or merged")
            # The plain-scalar choice only pays off if PATTERN_RX still sees them.
            self.assertEqual(sum(pd_errlog.pattern_counts(text).values()), self.N // 4,
                             f"seed {seed}: PATTERN_RX lost an entry")

    def test_degenerate_yaml_tokens_are_neutralized(self) -> None:
        """`=` carries YAML's value tag and makes SafeLoader raise on the whole file."""
        for token in ("=", "~", "null", "NULL", "   ", "'''", "[[["):
            self.assertEqual(pd_errlog._yaml_plain(token), "unknown", f"token {token!r}")
        # Number- and boolean-shaped IDs are realistic and left intact.
        for token in ("3", "no", "hw4-p3"):
            self.assertEqual(pd_errlog._yaml_plain(token), token)

    def test_a_special_char_behind_whitespace_is_still_stripped(self) -> None:
        """lstrip-then-strip halts at the space and re-exposes the next indicator."""
        self.assertEqual(pd_errlog._yaml_plain("'\n[`.\x0c>xD6"), ". >xD6")

    def test_meta_values_never_forge_a_line(self) -> None:
        rng = random.Random(13)
        for _ in range(self.N):
            pd_meta.write_meta(self.cwd, {k: self._rand(rng, 40) for k in pd_meta.META_KEYS})
            raw = (self.cwd / ".course-meta").read_text(encoding="utf-8")
            self.assertEqual(
                len(raw.strip().splitlines()), len(pd_meta.META_KEYS),
                "a value forged an extra KEY: value line",
            )


class TestAtomicMeta(TempCourse):
    def test_write_meta_is_atomic(self) -> None:
        """A failed write must leave the previous .course-meta intact.

        .course-meta's existence is what marks the folder as a course, so a
        truncated survivor is worse than no write at all.
        """
        self.scaffold()
        original = (self.cwd / ".course-meta").read_text(encoding="utf-8")

        class Boom(Exception):
            pass

        real_replace = os.replace

        def exploding_replace(src, dst):
            raise Boom("disk died mid-rename")

        os.replace = exploding_replace
        try:
            with self.assertRaises(Boom):
                pd_meta.write_meta(self.cwd, {"COURSE_NAME": "Clobbered"})
        finally:
            os.replace = real_replace

        self.assertEqual((self.cwd / ".course-meta").read_text(encoding="utf-8"), original)
        self.assertEqual(pd_meta.parse_meta(self.cwd)["COURSE_NAME"], "Complex Analysis")
        leftovers = [p.name for p in self.cwd.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [], "temp file leaked on failure")

    def test_atomic_write_matches_what_open_would_have_done(self) -> None:
        """mkstemp() is 0600, but hardcoding 0644 overrides a strict umask.

        Both directions are wrong: silently privatising files the user may share,
        or silently widening them past the umask they deliberately set.
        """
        for umask in (0o022, 0o077, 0o002):
            old = os.umask(umask)
            try:
                course = self.cwd / f"u{umask:03o}"
                course.mkdir()
                pd_meta.write_meta(course, {"COURSE_NAME": "X"})
                reference = course / "ref.txt"
                reference.write_text("x", encoding="utf-8")   # plain open()
                self.assertEqual(
                    (course / ".course-meta").stat().st_mode & 0o777,
                    reference.stat().st_mode & 0o777,
                    f"umask {umask:03o}: atomic write disagrees with open()",
                )
            finally:
                os.umask(old)

    def test_rewrite_preserves_an_explicit_mode(self) -> None:
        self.scaffold()
        meta = self.cwd / ".course-meta"
        os.chmod(meta, 0o640)
        pd_meta.write_meta(self.cwd, {"COURSE_NAME": "Y"})
        self.assertEqual(meta.stat().st_mode & 0o777, 0o640, "rewrite lost the mode")

    def test_control_characters_never_reach_the_terminal(self) -> None:
        """COURSE_NAME is echoed by the session banner and the status line.

        An escape sequence that survives the writer is written to the user's
        terminal on every session start in that folder.
        """
        banner = importlib.import_module("hermes_plugins.paideia.pd_banner")
        pd_meta.write_meta(self.cwd, {
            "COURSE_NAME": "Algebra\x1b[31m\x07 \x00bell", "EXAM_DATE": "2099-01-01",
        })
        name = pd_meta.parse_meta(self.cwd)["COURSE_NAME"]
        surfaces = [name, pd_status.render_status(self.cwd), banner.render_banner(self.cwd)]
        for text in surfaces:
            for ch in text:
                self.assertFalse(
                    ord(ch) < 0x20 and ch != "\n" or ord(ch) == 0x7F,
                    f"control char {ch!r} survived into {text!r}",
                )
        self.assertIn("Algebra", name)

    def test_roundtrip_preserves_unknown_keys(self) -> None:
        pd_meta.write_meta(self.cwd, {"COURSE_NAME": "X", "CUSTOM_KEY": "kept"})
        self.assertEqual(pd_meta.parse_meta(self.cwd)["CUSTOM_KEY"], "kept")

    def test_trailing_comment_is_stripped(self) -> None:
        (self.cwd / ".course-meta").write_text(
            "COURSE_NAME: Complex Analysis  # main course\nINTERFACE_LANG: ko\n",
            encoding="utf-8",
        )
        self.assertEqual(pd_meta.parse_meta(self.cwd)["COURSE_NAME"], "Complex Analysis")
        self.assertEqual(pd_meta.read_lang(self.cwd), "ko")

    def test_a_newline_in_a_value_cannot_forge_a_key(self) -> None:
        """.course-meta is line-oriented; a value must stay on its line.

        Otherwise `weak="x\\nEXAM_DATE: 1999-01-01"` writes a second key the
        reader treats as real, and the intended value is silently truncated.
        """
        pd_meta.write_meta(self.cwd, {
            "COURSE_NAME": "Real Analysis\nEXAM_DATE: 1999-01-01",
            "EXAM_DATE": "2099-08-30",
            "USER_WEAK_ZONES": "contours\r\nOCR_ENGINE: bogus",
            "OCR_ENGINE": "claude",
            "INTERFACE_LANG": "en",
        })
        raw = (self.cwd / ".course-meta").read_text(encoding="utf-8")
        self.assertEqual(len(raw.strip().splitlines()), len(pd_meta.META_KEYS))

        meta = pd_meta.parse_meta(self.cwd)
        self.assertEqual(meta["EXAM_DATE"], "2099-08-30")
        self.assertEqual(meta["OCR_ENGINE"], "claude")
        self.assertIn("Real Analysis", meta["COURSE_NAME"])
        self.assertIn("1999-01-01", meta["COURSE_NAME"])   # kept, not lost

    def test_no_line_break_character_can_forge_a_key(self) -> None:
        """Every char str.splitlines() breaks on, not just `\\n`.

        `\\x85`, `\\u2028` and `\\u2029` are outside the control-char class and are
        caught only by `\\s` — narrowing that whitespace collapse in a future
        refactor would quietly reopen the key-forging hole.
        """
        breaks = ["\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e",
                  "\x85", " ", " "]
        self.assertEqual(
            len("A\nB".splitlines()), 2, "sanity: splitlines splits on these"
        )
        for ch in breaks:
            self.assertEqual(
                len(f"A{ch}B".splitlines()), 2, f"{ch!r} is not a line break after all"
            )
            pd_meta.write_meta(self.cwd, {
                "COURSE_NAME": f"A{ch}EXAM_DATE: 1999-01-01",
                "EXAM_DATE": "2099-08-30",
            })
            raw = (self.cwd / ".course-meta").read_text(encoding="utf-8")
            self.assertEqual(
                len(raw.strip().splitlines()), len(pd_meta.META_KEYS),
                f"{ch!r} forged a key line",
            )
            self.assertEqual(pd_meta.parse_meta(self.cwd)["EXAM_DATE"], "2099-08-30")

    def test_hash_inside_a_value_is_not_a_comment(self) -> None:
        """Only the documented `value  # note` form is a comment.

        Looser rules eat real text: a bare `#` turns `C# Programming` into `C`,
        and a single space turns `Complex Analysis #2` into `Complex Analysis`.
        """
        cases = {
            "C# Programming": "C# Programming",
            "Complex Analysis #2": "Complex Analysis #2",
            "Complex Analysis  # main course": "Complex Analysis",
            "Complex Analysis\t# note": "Complex Analysis",
            "# just a comment": "",
            "Algebra": "Algebra",
        }
        for raw, expected in cases.items():
            self.assertEqual(pd_meta.strip_comment(raw), expected, f"input {raw!r}")

    def test_meta_write_read_is_lossless(self) -> None:
        """Whatever write_meta stores, parse_meta must hand back unchanged.

        _flatten collapses whitespace runs to one space, so a written value can
        never come back looking like a comment — that is what makes the comment
        threshold safe rather than merely lucky.
        """
        values = [
            "Complex Analysis #2", "C# Programming", "Physics I — §3 #a",
            "미적분학 #2 (심화)", "a  b   c", "x#y#z", "trailing space ",
        ]
        for v in values:
            pd_meta.write_meta(self.cwd, {"COURSE_NAME": v, "EXAM_DATE": "2099-01-01"})
            got = pd_meta.parse_meta(self.cwd)["COURSE_NAME"]
            self.assertEqual(got, pd_meta._flatten(v), f"round-trip lost {v!r}")
            self.assertNotIn("  ", got, "a written value could be misread as a comment")

    def test_all_three_meta_parsers_agree(self) -> None:
        """pd_doctor and pd_vision_ocr keep standalone copies of the comment rule."""
        for raw, expected in (("C# Programming", "C# Programming"),
                              ("Complex Analysis  # main", "Complex Analysis"),
                              ("Algebra", "Algebra")):
            (self.cwd / ".course-meta").write_text(
                f"COURSE_NAME: {raw}\nINTERFACE_LANG: ko  # bilingual\n",
                encoding="utf-8",
            )
            self.assertEqual(pd_meta.parse_meta(self.cwd)["COURSE_NAME"], expected)
            self.assertEqual(pd_doctor._parse_meta(self.cwd)["COURSE_NAME"], expected)
            self.assertEqual(pd_vision_ocr.read_course_name(self.cwd), expected)
            self.assertEqual(pd_meta.read_lang(self.cwd), "ko")
            self.assertEqual(pd_vision_ocr.read_interface_lang(self.cwd), "ko")

    def test_invalid_enums_fall_back(self) -> None:
        pd_meta.write_meta(self.cwd, {"INTERFACE_LANG": "fr", "OCR_ENGINE": "gpt"})
        self.assertEqual(pd_meta.read_lang(self.cwd), "en")
        self.assertEqual(pd_meta.read_ocr_engine(self.cwd), "claude")

    def test_days_until_rejects_garbage(self) -> None:
        for bad in ("", "tomorrow", "2026-13-01", "2026-02-30", "01-01-2026", None):
            self.assertIsNone(pd_meta.days_until(bad), f"accepted {bad!r}")
        self.assertIsNotNone(pd_meta.days_until("2026-08-30"))

    def test_fmt_days_signs(self) -> None:
        self.assertEqual(pd_meta.fmt_days(0), "D-0")
        self.assertEqual(pd_meta.fmt_days(5), "D-5")
        self.assertEqual(pd_meta.fmt_days(-3), "D+3")
        self.assertIsNone(pd_meta.fmt_days(None))


class TestGlobMetacharacterFolder(TempCourse):
    """A course folder named like a glob pattern must still work.

    Regression: glob.glob() treated the *course path* as part of the pattern, so
    "Math [2026] Final" matched nothing and the phase silently degraded.
    """

    folder_name = "Math [2026] Final"

    def test_phase_and_weakmap_still_resolve(self) -> None:
        self.scaffold()
        (self.cwd / "course-index" / "patterns.md").write_text("P1", encoding="utf-8")
        (self.cwd / "quizzes" / "topic_2026-01-01_0900.md").write_text("Q", encoding="utf-8")
        pd_errlog.append_error(
            self.cwd, problem_id="q1", pattern="P1", error_type="sign",
            summary="x", source="s.md",
        )
        self.assertTrue(pd_status._quiz_problems_exist(self.cwd))
        self.assertEqual(pd_status.detect_phase(self.cwd, 10), "drill")

        wm = self.cwd / "weakmap" / "weakmap_2026-01-02_1000.md"
        wm.write_text("## One-line verdict\n\nDrill P1 first.\n", encoding="utf-8")
        self.assertEqual(pd_weakmap.latest_weakmap(self.cwd), wm)
        self.assertEqual(pd_weakmap.latest_verdict(self.cwd), "Drill P1 first.")

    def test_answers_only_quizzes_do_not_count(self) -> None:
        self.scaffold()
        (self.cwd / "quizzes" / "t_answers.md").write_text("A", encoding="utf-8")
        self.assertFalse(pd_status._quiz_problems_exist(self.cwd))


class TestWeakmapOrdering(TempCourse):
    def test_latest_is_by_filename_not_mtime(self) -> None:
        """Name order, so a git clone (which resets every mtime) can't scramble it."""
        self.scaffold()
        old = self.cwd / "weakmap" / "weakmap_2026-01-01_0900.md"
        new = self.cwd / "weakmap" / "weakmap_2026-06-01_1200.md"
        new.write_text("## One-line verdict\n\nnewest\n", encoding="utf-8")
        old.write_text("## One-line verdict\n\noldest\n", encoding="utf-8")
        os.utime(old, (10**9, 10**9))          # old file, freshest mtime
        os.utime(new, (10**8, 10**8))
        self.assertEqual(pd_weakmap.latest_weakmap(self.cwd), new)
        self.assertEqual(pd_weakmap.latest_verdict(self.cwd), "newest")

    def test_top_miss_prefers_weakmap_then_falls_back(self) -> None:
        self.scaffold()
        pd_errlog.append_error(
            self.cwd, problem_id="q1", pattern="P2", error_type="sign",
            summary="x", source="s.md",
        )
        self.assertEqual(pd_weakmap.top_miss(self.cwd), "P2")   # no weakmap yet
        (self.cwd / "weakmap" / "weakmap_2026-01-01_0900.md").write_text(
            "# Weakmap\n\npattern: P5 is the worst\n", encoding="utf-8"
        )
        self.assertEqual(pd_weakmap.top_miss(self.cwd), "P5")

    def test_no_weakmap_dir_is_not_an_error(self) -> None:
        self.assertIsNone(pd_weakmap.latest_weakmap(self.cwd))
        self.assertIsNone(pd_weakmap.latest_verdict(self.cwd))


class TestPhaseDetection(TempCourse):
    def test_phase_progression(self) -> None:
        self.scaffold()
        self.assertEqual(pd_status.detect_phase(self.cwd, 30), "setup")

        (self.cwd / "course-index" / "patterns.md").write_text("P1", encoding="utf-8")
        self.assertEqual(pd_status.detect_phase(self.cwd, 30), "diag")

        (self.cwd / "quizzes" / "t_2026-01-01_0900.md").write_text("Q", encoding="utf-8")
        pd_errlog.append_error(
            self.cwd, problem_id="q1", pattern="P1", error_type="sign",
            summary="x", source="s.md",
        )
        self.assertEqual(pd_status.detect_phase(self.cwd, 30), "drill")

        pd_errlog.append_error(
            self.cwd, problem_id="mock_1", pattern="P2", error_type="sign",
            summary="x", source="answers/converted/mock_2026.md",
        )
        self.assertEqual(pd_status.detect_phase(self.cwd, 30), "mock")

        (self.cwd / "cheatsheet" / "final.md").write_text("c", encoding="utf-8")
        self.assertEqual(pd_status.detect_phase(self.cwd, 30), "cram")

        self.assertEqual(pd_status.detect_phase(self.cwd, 0), "cool")

    def test_status_line_shape(self) -> None:
        self.scaffold(EXAM_DATE="2099-01-01")
        line = pd_status.render_status(self.cwd)
        self.assertTrue(line.startswith("paideia · Complex Analysis · D-"))
        self.assertIn("setup", line)

    def test_status_outside_a_course(self) -> None:
        self.assertIn("not a course folder", pd_status.render_status(self.cwd))

    def test_long_course_name_is_truncated(self) -> None:
        self.scaffold(COURSE_NAME="A" * 80)
        self.assertIn("…", pd_status.render_status(self.cwd))


class TestScaffold(TempCourse):
    def test_gitignore_covers_the_archive(self) -> None:
        """grade.md promises graded scans stay out of git; make that true."""
        self.scaffold()
        text = (self.cwd / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("answers/_archive/", text)

    def test_gitignore_is_patched_not_clobbered(self) -> None:
        gi = self.cwd / ".gitignore"
        gi.write_text("# my own rules\nsecrets.txt\n", encoding="utf-8")
        self.scaffold()
        text = gi.read_text(encoding="utf-8")
        self.assertIn("secrets.txt", text)          # user content survives
        self.assertIn("answers/_archive/", text)    # ours is appended

    def test_gitignore_patch_is_idempotent(self) -> None:
        self.scaffold()
        first = (self.cwd / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(pd_workspace.ensure_gitignore(self.cwd), [])
        self.assertEqual((self.cwd / ".gitignore").read_text(encoding="utf-8"), first)

    def test_full_skeleton_and_seeds(self) -> None:
        report = self.scaffold()
        for rel in pd_workspace.SKELETON:
            self.assertTrue((self.cwd / rel).is_dir(), f"missing dir {rel}")
        self.assertTrue((self.cwd / "errors" / "log.md").is_file())
        self.assertTrue((self.cwd / "PAIDEIA.md").is_file())
        self.assertTrue(pd_workspace.is_course(self.cwd))
        self.assertIn("Complex Analysis", (self.cwd / "PAIDEIA.md").read_text(encoding="utf-8"))
        del report

    def test_rescaffold_preserves_the_error_log(self) -> None:
        self.scaffold()
        pd_errlog.append_error(
            self.cwd, problem_id="q1", pattern="P1", error_type="sign",
            summary="x", source="s.md",
        )
        self.scaffold()
        self.assertIn("problem_id: q1", pd_errlog.read_errors(self.cwd))


class TestDispatch(TempCourse):
    def test_init_rejects_a_bad_exam_date(self) -> None:
        """Better a loud refusal than a course whose countdown never appears."""
        cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            out = pd_commands.dispatch('init name="X" exam=2026-13-45')
        finally:
            os.chdir(cwd)
        self.assertIn("not a valid date", out)
        self.assertFalse((self.cwd / ".course-meta").exists(), "scaffolded anyway")

    def test_init_accepts_a_good_date(self) -> None:
        cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            out = pd_commands.dispatch('init name="X" exam=2099-08-30 lang=ko')
        finally:
            os.chdir(cwd)
        self.assertIn("✓", out)
        self.assertEqual(pd_meta.parse_meta(self.cwd)["EXAM_DATE"], "2099-08-30")

    def test_ack_names_no_provider(self) -> None:
        """hermes is model-agnostic; naming one provider is wrong for the rest."""
        for lang in ("en", "ko"):
            ack = pd_commands._ack("quiz", self.cwd, lang)
            self.assertNotIn("codex", ack.lower())
            self.assertNotIn("claude", ack.lower())

    def test_llm_sub_outside_a_course_refuses(self) -> None:
        cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            self.assertIn("not a PAIDEIA course folder", pd_commands.dispatch("quiz all 5"))
        finally:
            os.chdir(cwd)

    def test_unknown_sub_and_help(self) -> None:
        cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            self.assertIn("unknown subcommand", pd_commands.dispatch("nope"))
            self.assertIn("/paideia", pd_commands.dispatch(""))
            self.assertIn("/paideia", pd_commands.dispatch("help"))
        finally:
            os.chdir(cwd)

    def test_dispatch_never_raises(self) -> None:
        """The host CLI must survive any argument we can be handed."""
        cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            for raw in (None, "", "   ", 'init name="unclosed', "quiz " + "x" * 5000,
                        "status", "doctor", "help --nonsense"):
                self.assertIsInstance(pd_commands.dispatch(raw), str)
        finally:
            os.chdir(cwd)


class TestPrompts(unittest.TestCase):
    def test_every_llm_sub_has_a_spec(self) -> None:
        for sub in sorted(pd_commands.LLM_SUBS):
            self.assertIsNotNone(pd_prompts.load_spec(sub), f"commands/{sub}.md missing")

    def test_every_llm_sub_maps_to_real_skills(self) -> None:
        for sub in sorted(pd_commands.LLM_SUBS):
            self.assertIn(sub, pd_prompts.SKILL_FOR, f"{sub} has no skill mapping")
            for d in pd_prompts.SKILL_FOR[sub]:
                self.assertTrue(
                    (REPO / "skills" / d / "SKILL.md").is_file(),
                    f"{sub} maps to missing skill {d}",
                )

    def test_interactive_init_spec_exists(self) -> None:
        self.assertIsNotNone(pd_prompts.load_spec("init-course"))

    def test_plugin_root_placeholder_is_resolved(self) -> None:
        """Specs must never hand the agent a literal ${PAIDEIA_PLUGIN_ROOT}."""
        for sub in sorted(pd_commands.LLM_SUBS):
            msg = pd_prompts.build_inject(sub, "", Path("/tmp/course"), "en")
            self.assertNotIn("${PAIDEIA_PLUGIN_ROOT}", msg, f"{sub} leaks the placeholder")

    def test_load_spec_refuses_to_traverse(self) -> None:
        """Callers pre-validate, but the string starts life as chat input."""
        for sub in ("../pd_meta", "../../etc/passwd", "..", ".hidden",
                    "skills/paideia-pdf/SKILL", "", "a\\b"):
            self.assertIsNone(pd_prompts.load_spec(sub), f"traversed with {sub!r}")

    def test_inject_header_names_both_marker_vocabularies(self) -> None:
        """analyze.md defines two; downstream tools regex on both."""
        msg = pd_prompts.build_inject("analyze", "", Path("/tmp/c"), "ko")
        for marker in ("🔥🔥", "⚪", "✅✅", "🔴🔴"):
            self.assertIn(marker, msg, f"{marker} missing from the inject header")

    def test_every_plugin_rooted_path_in_a_rendered_turn_exists(self) -> None:
        """The rendered turn is what the agent actually acts on.

        Covers more than the spec-file scan: the skill bullets build_inject adds
        itself, and any path a spec composes from the resolved plugin root. If
        one is missing the agent burns a turn on a read that cannot succeed.
        """
        import re

        root = str(pd_prompts.PLUGIN_ROOT)
        broken: list[str] = []
        for sub in sorted(pd_commands.LLM_SUBS | {"init-course"}):
            msg = pd_prompts.build_inject(sub, "", Path("/course"), "en")
            for path in sorted(set(re.findall(re.escape(root) + r"[\w/.-]*", msg))):
                if not Path(path).exists():
                    broken.append(f"{sub}: {path}")
        self.assertEqual(broken, [], "rendered turn points at files that don't exist")

    def test_gateway_path_tolerates_unknown_cwd(self) -> None:
        msg = pd_prompts.build_inject("quiz", "all 5", None, None)
        self.assertIn("INTERFACE_LANG", msg)
        self.assertIn("Arguments: all 5", msg)


class TestSpecReferences(unittest.TestCase):
    """Specs are instructions to an agent — a wrong reference becomes a wrong action.

    These catch the class of bug where prose and code drift: a spec telling the
    user to run a subcommand the dispatcher rejects, or to execute a bundled
    script that isn't shipped.
    """

    @staticmethod
    def _spec_files() -> list[Path]:
        return sorted((REPO / "commands").glob("*.md")) + sorted(
            (REPO / "skills").rglob("*.md")
        )

    def test_every_referenced_subcommand_is_dispatchable(self) -> None:
        import re

        valid = pd_commands.LLM_SUBS | pd_commands.DETERMINISTIC
        bad: list[str] = []
        for path in self._spec_files():
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r"/paideia\s+([a-zA-Z][\w-]*)", text):
                sub = m.group(1).lower()
                if sub not in valid:
                    bad.append(f"{path.relative_to(REPO)}: /paideia {sub}")
        self.assertEqual(
            bad, [],
            "spec references a subcommand the dispatcher rejects "
            f"(valid: {sorted(valid)})",
        )

    def test_every_referenced_bundled_script_exists(self) -> None:
        import re

        bad: list[str] = []
        for path in self._spec_files():
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r"\$\{PAIDEIA_PLUGIN_ROOT\}/([\w./-]+)", text):
                target = m.group(1)
                if not (REPO / target).exists():
                    bad.append(f"{path.relative_to(REPO)}: {target}")
        self.assertEqual(bad, [], "spec invokes a script that is not shipped")

    def test_render_script_is_actually_wired_in(self) -> None:
        """pd_render.py shipped unreferenced once; keep it reachable."""
        referenced = [
            p.relative_to(REPO).as_posix()
            for p in self._spec_files()
            if "pd_render.py" in p.read_text(encoding="utf-8")
        ]
        self.assertIn("commands/ingest.md", referenced)
        self.assertIn("commands/grade.md", referenced)

    def test_readmes_document_every_command_and_count_them_right(self) -> None:
        """Both READMEs table every dispatchable command, and the heading agrees.

        `help` is excluded: it is the listing itself, not an entry in it.
        """
        import re

        expected = (pd_commands.LLM_SUBS | pd_commands.DETERMINISTIC) - {"help"}
        for name, heading in (("README.md", r"##\s*Commands\s*\((\d+) total\)"),
                              ("README.ko.md", r"##\s*명령어\s*\(총\s*(\d+)개\)")):
            text = (REPO / name).read_text(encoding="utf-8")
            m = re.search(heading, text)
            self.assertIsNotNone(m, f"{name}: no command-count heading")
            table = re.findall(r"^\|\s*`/paideia ([a-z-]+)", text, re.MULTILINE)
            self.assertEqual(set(table), expected, f"{name}: table misses a command")
            self.assertEqual(
                int(m.group(1)), len(expected),
                f"{name}: heading says {m.group(1)}, {len(expected)} commands exist",
            )

    def test_hwmap_has_no_blind_spot_mode(self) -> None:
        """`blind` is a legacy alias for `hot`, not a blind-spot listing.

        Treating it as one inverts the plugin's core thesis: a section with no HW
        is the professor signalling it is off the exam, not a hazard to drill.
        """
        hwmap = (REPO / "commands" / "hwmap.md").read_text(encoding="utf-8")
        self.assertIn("backwards compatibility", hwmap)
        offenders = [
            path.relative_to(REPO).as_posix()
            for path in self._spec_files()
            if "/paideia hwmap blind" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            offenders, [],
            "these send the user to a mode that returns exam-hot zones, "
            "not blind spots",
        )


class TestGatewayHook(unittest.TestCase):
    """`/paideia <sub>` typed into Slack/Discord must reach the agent."""

    def _hook(self):
        captured = {}

        class Ctx:
            def register_command(self, *a, **k): pass
            def register_hook(self, name, fn): captured[name] = fn

        PLUGIN.register(Ctx())
        self.assertIn("on_session_start", captured, "banner hook not registered")
        return captured["pre_gateway_dispatch"]

    def test_llm_sub_is_rewritten(self) -> None:
        hook = self._hook()
        for text in ("/paideia quiz all 5", "!paideia quiz all 5", "paideia QUIZ all 5"):
            result = hook(event=types.SimpleNamespace(text=text))
            self.assertIsNotNone(result, f"{text!r} not intercepted")
            self.assertEqual(result["action"], "rewrite")
            self.assertIn("PAIDEIA · /paideia quiz", result["text"])

    def test_deterministic_subs_fall_through(self) -> None:
        hook = self._hook()
        for sub in ("status", "doctor", "help", "init"):
            self.assertIsNone(hook(event=types.SimpleNamespace(text=f"/paideia {sub}")))

    def test_unrelated_text_falls_through(self) -> None:
        hook = self._hook()
        for text in ("hello there", "/other quiz", "", "paideia"):
            self.assertIsNone(hook(event=types.SimpleNamespace(text=text)))

    def test_hook_never_raises(self) -> None:
        hook = self._hook()
        self.assertIsNone(hook(event=None))
        self.assertIsNone(hook(event=types.SimpleNamespace()))


class TestDoctorContracts(unittest.TestCase):
    """pd_doctor keeps standalone copies of shared data — pin them to the source."""

    def test_skeleton_matches_workspace(self) -> None:
        self.assertEqual(tuple(pd_doctor.SKELETON), tuple(pd_workspace.SKELETON))

    def test_meta_keys_match(self) -> None:
        self.assertEqual(tuple(pd_doctor.META_KEYS), tuple(pd_meta.META_KEYS))

    def test_errors_seed_matches(self) -> None:
        self.assertEqual(pd_doctor._ERRORS_LOG_SEED, pd_workspace.ERRORS_LOG_SEED)

    def test_enum_lists_match(self) -> None:
        self.assertEqual(set(pd_meta.VALID_OCR), {"claude", "ollama", "tesseract"})
        self.assertEqual(set(pd_meta.VALID_LANG), {"en", "ko"})

    def test_payload_list_matches_disk(self) -> None:
        on_disk = {p.stem for p in (REPO / "commands").glob("*.md")}
        self.assertEqual(set(pd_doctor.PAYLOAD_COMMANDS), on_disk)
        skills = {p.parent.name for p in (REPO / "skills").glob("*/SKILL.md")}
        self.assertEqual(set(pd_doctor.PAYLOAD_SKILLS), skills)
        for script in pd_doctor.PAYLOAD_SCRIPTS:
            self.assertTrue((REPO / script).is_file(), f"{script} not shipped")

    def test_payload_covers_every_dispatchable_sub(self) -> None:
        self.assertTrue(
            pd_commands.LLM_SUBS <= set(pd_doctor.PAYLOAD_COMMANDS),
            "an LLM subcommand has no spec in the payload list",
        )

    def test_required_deps_are_disjoint_from_optional(self) -> None:
        self.assertFalse(set(pd_doctor.REQUIRED_PY_DEPS) & set(pd_doctor.OPTIONAL_PY_DEPS))

    def test_doctor_runs_clean_on_this_checkout(self) -> None:
        code, report = pd_doctor.run(REPO, fix=False)
        self.assertIn("plugin:payload", report)
        self.assertNotIn("✗ plugin:payload", report)
        self.assertLessEqual(code, 1, report)

    def test_doctor_fix_repairs_a_course(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="paideia-doc-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        pd_meta.write_meta(tmp, {
            "COURSE_NAME": "X", "EXAM_DATE": "2099-01-01", "EXAM_TYPE": "final",
            "USER_WEAK_ZONES": "n", "OCR_ENGINE": "claude", "INTERFACE_LANG": "en",
        })
        pd_doctor.run(tmp, fix=True)
        for rel in pd_doctor.SKELETON:
            self.assertTrue((tmp / rel).is_dir(), f"--fix left {rel} missing")
        self.assertTrue((tmp / "errors" / "log.md").is_file())

    def test_doctor_flags_an_invalid_engine(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="paideia-doc-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        pd_meta.write_meta(tmp, {"COURSE_NAME": "X", "OCR_ENGINE": "gpt-vision"})
        code, report = pd_doctor.run(tmp, fix=False)
        self.assertIn("meta:OCR_ENGINE", report)
        self.assertEqual(code, 2)


class TestBrokenCourseMeta(TempCourse):
    """A present-but-unreadable .course-meta must not read as "no course".

    All four surfaces used to disagree: is_course() said yes so the LLM
    subcommands ran, status said "not a course folder — run /paideia init"
    (which would overwrite the remains), the banner went silent, and doctor —
    the tool you run to diagnose this — reported "all clear" while skipping
    every workspace check.
    """

    def setUp(self) -> None:
        super().setUp()
        (self.cwd / ".course-meta").write_text("", encoding="utf-8")

    def test_status_points_at_doctor_not_init(self) -> None:
        line = pd_status.render_status(self.cwd)
        self.assertIn("doctor", line)
        self.assertNotIn("init", line)

    def test_banner_is_not_silent(self) -> None:
        banner = importlib.import_module("hermes_plugins.paideia.pd_banner")
        text = banner.render_banner(self.cwd)
        self.assertIsNotNone(text)
        self.assertIn("doctor", text)

    def test_doctor_fails_and_checks_the_workspace(self) -> None:
        code, report = pd_doctor.run(self.cwd, fix=False)
        self.assertEqual(code, 2, report)
        self.assertIn("meta:.course-meta", report)
        self.assertIn("workspace:", report)

    def test_doctor_fix_still_repairs_what_it_can(self) -> None:
        pd_doctor.run(self.cwd, fix=True)
        self.assertTrue((self.cwd / "errors" / "log.md").is_file())
        for rel in pd_doctor.SKELETON:
            self.assertTrue((self.cwd / rel).is_dir(), f"--fix left {rel} missing")

    def test_a_real_absence_still_reads_as_no_course(self) -> None:
        (self.cwd / ".course-meta").unlink()
        self.assertIn("not a course folder", pd_status.render_status(self.cwd))
        banner = importlib.import_module("hermes_plugins.paideia.pd_banner")
        self.assertIsNone(banner.render_banner(self.cwd))
        self.assertLessEqual(pd_doctor.run(self.cwd)[0], 1)


class TestBanner(TempCourse):
    def test_silent_outside_a_course(self) -> None:
        banner = importlib.import_module("hermes_plugins.paideia.pd_banner")
        self.assertIsNone(banner.render_banner(self.cwd))

    def test_bilingual_next_step(self) -> None:
        banner = importlib.import_module("hermes_plugins.paideia.pd_banner")
        self.scaffold(INTERFACE_LANG="ko")
        text = banner.render_banner(self.cwd)
        self.assertIn("[paideia]", text)
        self.assertIn("다음:", text)

        self.scaffold(INTERFACE_LANG="en")
        self.assertIn("next:", banner.render_banner(self.cwd))

    def test_verdict_wins_over_top_miss(self) -> None:
        banner = importlib.import_module("hermes_plugins.paideia.pd_banner")
        self.scaffold()
        pd_errlog.append_error(
            self.cwd, problem_id="q1", pattern="P4", error_type="sign",
            summary="x", source="s.md",
        )
        (self.cwd / "weakmap" / "weakmap_2026-01-01_0900.md").write_text(
            "## One-line verdict\n\nContours, not residues.\n", encoding="utf-8"
        )
        self.assertIn("Contours, not residues.", banner.render_banner(self.cwd))


class TestRenderScripts(unittest.TestCase):
    """pd_render is the single render path; pd_vision_ocr must page-order alike."""

    def test_page_number_padding_scales(self) -> None:
        """p100 must never sort between p10 and p11 — agents read sorted order."""
        for total, width in ((9, 2), (99, 2), (100, 3), (120, 3), (1000, 4)):
            computed = max(2, len(str(total)))
            self.assertEqual(computed, width, f"padding wrong for {total} pages")
            names = sorted(f"p{i:0{computed}d}.png" for i in range(1, total + 1))
            self.assertEqual(
                [int(n[1:-4]) for n in names], list(range(1, total + 1)),
                f"sorted order != page order at {total} pages",
            )

    def test_both_scripts_expose_streaming_iterators(self) -> None:
        for mod in (pd_render, pd_vision_ocr):
            self.assertTrue(callable(mod.iter_pages), f"{mod.__name__}.iter_pages")
            self.assertTrue(callable(mod.page_count), f"{mod.__name__}.page_count")

    def test_render_rejects_bad_args(self) -> None:
        for argv in (["x"], ["x", "only-one"], ["x", "a", "b", "c"],
                     ["x", "--dpi=0", "a.pdf", "out"]):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                pd_render._parse_args(argv)

    def test_non_numeric_flags_are_a_usage_error_not_a_traceback(self) -> None:
        """Same contract as an unreadable PDF: the agent must get a reason."""
        for argv in (["x", "--dpi=abc", "a.pdf", "out"],
                     ["x", "--max-px=", "a.pdf", "out"],
                     ["x", "--dpi=1.5", "a.pdf", "out"]):
            err = io.StringIO()
            with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(err):
                pd_render._parse_args(argv)
            self.assertEqual(cm.exception.code, 2, argv)
            self.assertIn("needs an integer", err.getvalue(), argv)

    def test_render_accepts_overrides(self) -> None:
        pdf, out, dpi, max_px = pd_render._parse_args(
            ["x", "--dpi=200", "--max-px=1200", "a.pdf", "out"]
        )
        self.assertEqual((str(pdf), str(out), dpi, max_px), ("a.pdf", "out", 200, 1200))

    def test_ocr_arg_parsing(self) -> None:
        engine, pdf, out, course, lang = pd_vision_ocr._parse_args(
            ["x", "--engine=tesseract", "--lang=ko", "--course-name=QM", "a.pdf", "b.md"]
        )
        self.assertEqual((engine, str(pdf), str(out), course, lang),
                         ("tesseract", "a.pdf", "b.md", "QM", "ko"))
        for argv in (["x", "--engine=gpt", "a.pdf", "b.md"],
                     ["x", "--lang=fr", "a.pdf", "b.md"],
                     ["x", "a.pdf"]):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                pd_vision_ocr._parse_args(argv)

    def test_prompt_contract_clauses_survive(self) -> None:
        """The six clauses are what separate transcription from hallucination."""
        prompt = pd_vision_ocr.build_prompt("Quantum Mechanics", "ko")
        for clause in ("LaTeX", "problem numbering", "Do NOT interpret",
                       "[?]", "crossed-out", "ONLY markdown"):
            self.assertIn(clause, prompt)
        self.assertIn("Quantum Mechanics", prompt)

    def test_dedupe_strips_vlm_self_talk(self) -> None:
        text = "Wait, let me look again. $x = 1$. The image shows a page. $x = 1$."
        out = pd_vision_ocr.dedupe_loops(text)
        self.assertIn("$x = 1$", out)
        self.assertNotIn("Wait,", out)
        self.assertNotIn("The image shows", out)


def _can_render() -> bool:
    """True when reportlab + pdf2image + poppler are all present."""
    try:
        import reportlab  # noqa: F401
        import pdf2image  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False
    return shutil.which("pdftoppm") is not None and shutil.which("pdfinfo") is not None


def _make_pdf(path: Path, pages: int) -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    for i in range(1, pages + 1):
        c.setFont("Helvetica", 36)
        c.drawString(100, 400, f"PAGE {i}")
        c.showPage()
    c.save()
    return path


@unittest.skipUnless(_can_render(), "needs reportlab + pdf2image + poppler")
class TestRenderEndToEnd(unittest.TestCase):
    """The real pipeline on a real PDF — the cheap logic tests can't catch these."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="paideia-render-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_over_99_pages_stay_in_order(self) -> None:
        """The regression: p100 sorting between p10 and p11 scrambles a chapter.

        A textbook chapter crossing 100 pages is ordinary, and the failure is
        silent — the agent transcribes real pages in a nonsense sequence.
        """
        pdf = _make_pdf(self.tmp / "big.pdf", 101)
        self.assertEqual(pd_render.page_count(pdf), 101)

        pages = pd_render.render_pdf_pages(pdf, self.tmp / "out", dpi=40, max_px=300)
        self.assertEqual(len(pages), 101)
        self.assertEqual(pages[0].name, "p001.png")
        self.assertEqual(pages[-1].name, "p101.png")

        # What the agent actually consumes: sorted filenames.
        on_disk = sorted(p.name for p in (self.tmp / "out").glob("*.png"))
        self.assertEqual(on_disk, [p.name for p in pages])

    def test_long_edge_is_capped(self) -> None:
        """No oversized PNG may ever reach disk — an agent that reads one is lost."""
        from PIL import Image

        pdf = _make_pdf(self.tmp / "small.pdf", 3)
        pages = pd_render.render_pdf_pages(pdf, self.tmp / "out", dpi=200, max_px=400)
        self.assertEqual(len(pages), 3)
        for p in pages:
            with Image.open(p) as im:
                self.assertLessEqual(max(im.size), 400, f"{p.name} exceeds the cap")

    def test_padding_is_right_when_the_page_count_is_unknown(self) -> None:
        """The poppler-can't-count fallback must not guess the padding width.

        A guessed width is how p1000.png ends up sorting before p999.png — the
        same silent scrambling the main path was fixed for.
        """
        pdf = _make_pdf(self.tmp / "opaque.pdf", 12)
        real = pd_render.page_count
        pd_render.page_count = lambda _p: 0          # simulate an unusable pdfinfo
        try:
            pages = pd_render.render_pdf_pages(pdf, self.tmp / "out", dpi=40, max_px=300)
        finally:
            pd_render.page_count = real
        self.assertEqual(len(pages), 12)
        self.assertEqual(pages[0].name, "p01.png")
        self.assertEqual(pages[-1].name, "p12.png")
        self.assertEqual(
            sorted(p.name for p in (self.tmp / "out").glob("*.png")),
            [p.name for p in pages],
        )

    def test_small_pdf_keeps_two_digit_padding(self) -> None:
        pdf = _make_pdf(self.tmp / "tiny.pdf", 3)
        pages = pd_render.render_pdf_pages(pdf, self.tmp / "out", dpi=40, max_px=300)
        self.assertEqual([p.name for p in pages], ["p01.png", "p02.png", "p03.png"])

    def test_streaming_holds_one_page_at_a_time(self) -> None:
        """iter_pages must not materialize the whole PDF (that is the OOM bug)."""
        pdf = _make_pdf(self.tmp / "seq.pdf", 12)
        seen = []
        for i, img in pd_render.iter_pages(pdf, dpi=40):
            seen.append(i)
            self.assertTrue(hasattr(img, "size"))
        self.assertEqual(seen, list(range(1, 13)))

    def test_ocr_writes_utf8_regardless_of_locale(self) -> None:
        """Korean transcriptions must survive a C/POSIX locale.

        Regression: write_text() without an explicit encoding uses the locale
        encoding, which mangles or hard-fails on non-ASCII output.
        """
        pdf = _make_pdf(self.tmp / "ko.pdf", 1)
        out = self.tmp / "out" / "ko.md"
        korean = "적분을 부분적분으로 풀었음"

        real = pd_vision_ocr.tesseract_fallback
        pd_vision_ocr.tesseract_fallback = lambda pages, lang=None: (
            "".join(f"## Page {i}\n\n{korean}\n" for i, _ in pages)
        )
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                pd_vision_ocr.ocr_pdf(pdf, out, engine="tesseract")
        finally:
            pd_vision_ocr.tesseract_fallback = real

        self.assertEqual(out.read_bytes().decode("utf-8").count(korean), 1)
        self.assertIn(korean, out.read_text(encoding="utf-8"))

    def test_unreadable_pdf_gets_an_actionable_error_not_a_traceback(self) -> None:
        """An agent reads this output; a pdf2image traceback tells it nothing.

        Both specs promise the caller can relay a specific reason to the user
        (password-protected / truncated / not a PDF), so the scripts have to
        actually say which.
        """
        bad = self.tmp / "corrupt.pdf"
        bad.write_text("this is definitely not a pdf", encoding="utf-8")

        for argv, name in (
            ([str(REPO / "pd_render.py"), str(bad), str(self.tmp / "o")], "pd_render"),
            ([str(REPO / "pd_vision_ocr.py"), "--engine=tesseract",
              str(bad), str(self.tmp / "o.md")], "pd_vision_ocr"),
        ):
            r = subprocess.run([sys.executable, *argv], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, f"{name}: expected exit 1\n{r.stderr}")
            self.assertNotIn("Traceback", r.stderr, f"{name} leaked a traceback")
            self.assertIn("password-protected", r.stderr, f"{name}: no remedy offered")
            self.assertIn("pdfinfo", r.stderr, f"{name}: no diagnostic offered")

    def test_missing_pdf_is_distinguished_from_an_unreadable_one(self) -> None:
        r = subprocess.run(
            [sys.executable, str(REPO / "pd_render.py"),
             str(self.tmp / "nope.pdf"), str(self.tmp / "o")],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 2, "a missing file is a usage error, not a bad PDF")
        self.assertIn("no such PDF", r.stderr)

    def test_ocr_page_order_matches_pd_render(self) -> None:
        """The two streaming iterators are separate copies — pin them together."""
        pdf = _make_pdf(self.tmp / "cmp.pdf", 7)
        self.assertEqual(
            [i for i, _ in pd_render.iter_pages(pdf, dpi=40)],
            [i for i, _ in pd_vision_ocr.iter_pages(pdf)],
        )
        self.assertEqual(pd_render.page_count(pdf), pd_vision_ocr.page_count(pdf))


def _require_yaml():
    try:
        import yaml
    except ImportError:  # pragma: no cover - environment-dependent
        raise unittest.SkipTest("pyyaml not installed; skipping YAML validity checks")
    return yaml


if __name__ == "__main__":
    unittest.main(verbosity=2)
