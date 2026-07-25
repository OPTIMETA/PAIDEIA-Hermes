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
import shutil
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

    def test_gateway_path_tolerates_unknown_cwd(self) -> None:
        msg = pd_prompts.build_inject("quiz", "all 5", None, None)
        self.assertIn("INTERFACE_LANG", msg)
        self.assertIn("Arguments: all 5", msg)


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
