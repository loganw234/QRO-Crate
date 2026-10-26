#!/bin/bash
# Copied from moth-quantum's verify/pytest-stage.sh at 3a73823 (study QRO-0, section 13's floor), unchanged below
# this line but for QRO-Crate's refusal of a pytest_plugins line, below; its last message, which names the
# runner's guards, need_file and need_env, the runner having no `need` (P0.4's verifier, round 4, note 9); and
# three options on the pytest line (P0.1's verifier, rounds 1 to 3):
#   - `-c pyproject.toml`: pytest reads the root's pyproject.toml and no other configuration file. Without it,
#     pytest takes the first one it finds among the test directory's ancestors, so a pytest.ini under tests/
#     took 327 tests out of their stage, which still passed (round 1, D1). With it, the rootdir is the root
#     (pytest 9.1.1, _pytest/config/findpaths.py, determine_setup);
#   - `--noconftest`: no conftest.py is read, anywhere. One under tests/ took 410 tests out of the run, the
#     registry's test that forbids it among them, and the run passed (round 2, R2-1);
#   - `--color=no`: FORCE_COLOR or PY_COLORS in the environment put colour codes in the summary line, which the
#     checks below then refused on a passing run (round 2, note 4.3.6).
# Run pytest on the given paths, and hold it to its own summary line as well
# as its exit code (METHOD §5: exit codes are not reports):
#   - rc must be 0;
#   - the last line must say "<n> passed", with n >= 1 (zero tests collected
#     passing is not a pass);
#   - the summary must name no failure and no error;
#   - the summary must name NO SKIP. A skip belongs to the runner, at stage
#     level, where it is printed by name and --require-all can see it. A test
#     that skips inside a stage passed the stage invisibly (verifier-P0 7e).
#     xfailed, xpassed and deselected are refused for the same reason: each
#     is a test the stage did not hold to its verdict.
#
# Third-party pytest plugins are switched off: a verdict must not depend on
# what happens to be installed (zarr's plugin imports CuPy on the owner's
# desktop, 2026-09-25).
set -uo pipefail
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
# Options from the environment are not the stage's: PYTEST_ADDOPTS=--ignore=...
# once passed golden on 35 of its 40 tests (verifier-P0's re-check).
unset PYTEST_ADDOPTS PYTEST_PLUGINS
# QRO-Crate's: a test module's pytest_plugins line loads a plugin into the stage, which can take tests out of
# it, the registry's own among them (P0.1's verifier, round 3, G3). Refused here, before pytest starts, where no
# test can reach. "$1" is the stage's directory: the registry holds each pytest stage to name one first.
plugins=$(grep -rlE --include='*.py' '^[[:space:]]*pytest_plugins[[:space:]]*[:=]' "$1" 2>/dev/null)
if [ -n "$plugins" ]; then
  echo "pytest-stage: a pytest_plugins line loads a plugin into the stage, and is refused: $plugins"
  exit 1
fi
out=$(python -m pytest -c pyproject.toml --noconftest --color=no -q -rs "$@" 2>&1)
rc=$?
echo "$out"
summary=$(printf '%s\n' "$out" | tail -n 1)
if [ "$rc" -ne 0 ]; then
  echo "pytest-stage: pytest exited $rc"
  exit 1
fi
if ! printf '%s\n' "$summary" | grep -Eq '^[1-9][0-9]* passed'; then
  echo "pytest-stage: no '<n> passed' summary line: $summary"
  exit 1
fi
if printf '%s\n' "$summary" | grep -Eq 'failed|error'; then
  echo "pytest-stage: the summary names a failure: $summary"
  exit 1
fi
if printf '%s\n' "$summary" | grep -Eq 'skipped|xpassed|deselected'; then
  echo "pytest-stage: the summary names a test this stage did not hold to a verdict: $summary"
  echo "pytest-stage: skip at stage level instead (need_file/need_env in verify/run.sh)"
  exit 1
fi
exit 0
