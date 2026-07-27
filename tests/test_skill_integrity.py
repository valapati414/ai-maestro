"""Structural guards for the storage_revenue_prediction skill.

These tests protect the properties that are easy to break by accident and that no
amount of careful forecasting arithmetic can compensate for: valid skill
frontmatter, reference files that actually exist, the dependency-light promise,
and an engine whose self-tests and worked example still run.

Stdlib only, so it runs with `python3 -m unittest` and needs nothing installed
beyond what the engine itself requires. pytest can also collect it.

    python3 -m unittest discover -s tests -v
    pytest tests/ -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "engine"

REFERENCES = (
    "variable-taxonomy.md",
    "with-order-flow.md",
    "without-order-flow.md",
    "probability-and-calibration.md",
    "demand-drivers-and-alt-data.md",
    "profit-levers.md",
    "company-profiles.md",
)

ENGINE_FILES = ("dpforecast.py", "test_dpforecast.py", "example_outside_in.py")

# Anything that would break the "runs anywhere" promise.
BANNED_IMPORTS = ("pandas", "sklearn", "scikit", "statsmodels", "matplotlib")

# The six parts of the output contract, in the order SKILL.md specifies.
OUTPUT_CONTRACT = (
    "1. HEADLINE",
    "2. THE SPLIT",
    "3. DECOMPOSITION",
    "4. MOST SENSITIVE ASSUMPTIONS",
    "5. ASSUMPTION REGISTER",
    "6. SCORING PLAN",
)


def has_numpy() -> bool:
    try:
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def run_engine(script: str) -> str:
    """Run an engine script from the engine directory and return its stdout."""
    proc = subprocess.run(
        [sys.executable, script],
        cwd=ENGINE,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"{script} exited {proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return proc.stdout


class TestSkillStructure(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_path = REPO / "SKILL.md"
        self.assertTrue(self.skill_path.is_file(), "SKILL.md is missing")
        self.skill = self.skill_path.read_text(encoding="utf-8")

    def test_frontmatter_is_valid(self) -> None:
        match = re.match(r"^---\n(.*?)\n---\n", self.skill, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md has no YAML frontmatter block")
        frontmatter = match.group(1)

        self.assertIn("name: data-protection-revenue-forecasting", frontmatter)
        self.assertRegex(frontmatter, r"(?m)^description: .+")

    def test_description_stays_specific(self) -> None:
        # The description is the only thing an agent sees when deciding whether to
        # load the skill, so it has to stay specific and third-person.
        match = re.search(r"description: (.+)", self.skill)
        self.assertIsNotNone(match)
        description = match.group(1)

        self.assertGreater(len(description), 80, "description is too vague to route on")
        self.assertLess(len(description), 1024, "description exceeds the frontmatter budget")
        self.assertIn("forecast", description.lower())

    def test_ships_every_reference_it_links_to(self) -> None:
        for ref in REFERENCES:
            with self.subTest(reference=ref):
                self.assertTrue(
                    (REPO / "references" / ref).is_file(),
                    f"references/{ref} is linked but missing",
                )
                self.assertIn(f"references/{ref}", self.skill)

    def test_ships_the_engine_its_tests_and_the_example(self) -> None:
        for name in ENGINE_FILES:
            with self.subTest(file=name):
                self.assertTrue((ENGINE / name).is_file(), f"engine/{name} is missing")

    def test_no_stale_paths_from_the_original_repo(self) -> None:
        # This skill was extracted from a larger repo where it lived under
        # .agents/skills/. Any surviving reference to that layout is a broken
        # instruction for anyone using this repo standalone.
        for path in [self.skill_path, *(REPO / "references").glob("*.md")]:
            with self.subTest(file=path.name):
                self.assertNotIn(".agents/skills", path.read_text(encoding="utf-8"))


class TestRepoIsSelfContained(unittest.TestCase):
    def test_has_the_files_a_standalone_repo_needs(self) -> None:
        for name in ("README.md", "LICENSE", "requirements.txt", ".gitignore"):
            with self.subTest(file=name):
                self.assertTrue((REPO / name).is_file(), f"{name} is missing")

    def test_readme_relative_links_resolve(self) -> None:
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\]\(\./([^)#]+)\)", readme)
        self.assertGreater(len(targets), 0, "README has no relative links to check")
        for target in targets:
            with self.subTest(link=target):
                self.assertTrue((REPO / target).exists(), f"README links to missing ./{target}")


class TestDependencyDiscipline(unittest.TestCase):
    def setUp(self) -> None:
        self.source = (ENGINE / "dpforecast.py").read_text(encoding="utf-8")
        self.top_level_imports = "\n".join(
            line
            for line in self.source.splitlines()
            if re.match(r"^(import|from) ", line)
        )

    def test_numpy_is_the_only_hard_dependency(self) -> None:
        self.assertIn("import numpy as np", self.top_level_imports)
        for banned in BANNED_IMPORTS:
            with self.subTest(package=banned):
                self.assertNotRegex(self.top_level_imports, rf"\b{banned}\b")

    def test_scipy_import_is_guarded(self) -> None:
        # scipy is a speed convenience, not a requirement, so it must stay inside
        # a try/except with a working fallback.
        self.assertRegex(self.source, r"try:[\s\S]{0,200}from scipy\.special import")


@unittest.skipUnless(has_numpy(), "numpy is not installed")
class TestEngineRuns(unittest.TestCase):
    example: str

    @classmethod
    def setUpClass(cls) -> None:
        # Run the example once and share it; it is seeded, so every run is identical
        # and test_is_deterministic below is what proves that.
        cls.example = run_engine("example_outside_in.py")

    def test_self_test_suite_passes(self) -> None:
        output = run_engine("test_dpforecast.py")
        self.assertIn("all self-tests passed", output)
        self.assertNotIn("FAIL", output)

    def test_worked_example_emits_the_full_output_contract(self) -> None:
        for section in OUTPUT_CONTRACT:
            with self.subTest(section=section):
                self.assertIn(section, self.example)

    def test_worked_example_never_reports_a_bare_point_estimate(self) -> None:
        # Iron Rule #2: every headline number ships with an interval.
        self.assertRegex(self.example, r"80% interval \$\d+M to \$\d+M")

    def test_worked_example_is_deterministic(self) -> None:
        # The example is seeded. If it drifts run to run, the numbers quoted in
        # SKILL.md and README.md silently stop matching what users see.
        self.assertEqual(
            self.example,
            run_engine("example_outside_in.py"),
            "the worked example is not reproducible",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
