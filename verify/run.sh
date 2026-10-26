#!/bin/bash
# QRO-Crate's front door: one command that answers "does it still hold?"
#
# Copied from moth-quantum's verify/run.sh at 3a73823 (study QRO-0, section 13's
# floor), which adapted HonestFramework's templates/gate-runner.sh. Its framework
# is kept line for line but for these, QRO-Crate's (P0's verifier, round 2):
#   - the header and its usage lines, the quick budget, the environment's
#     fingerprint and its message, and the stages;
#   - the `nocommit` case, below;
#   - -h prints this whole header, where it cut at a fixed line;
#   - the stage-name column is 17 characters wide, not 10, in --list and in
#     every note, for QRO-Crate's longer stage names, and --list puts a space
#     after it;
#   - comments that named Quantum-Film's own files or variables are reworded,
#     but for one, two lines on its golden stage above `packages=`, deleted;
#   - the command guard `need`, which nothing here called, is gone (P0.4's
#     verifier, round 3): need_file and need_env are kept.
# It keeps what the template argues for:
#   §3  a negative-control stage that must FAIL, for the reason it plants, and
#       fails the run if it passes; its positive twin must pass. So the runner
#       proves on every run that QRO-Crate's command line can say no to the
#       control's fault, and yes to its twin. That the runner counts any other
#       stage's failure, and exits 1 for it, the control's inverted verdict
#       cannot show: tests/docs/test_stage_registry.py runs the runner on a
#       copy whose lint fails (P0.4's verifier, round 4, note 5);
#   §4  the stage list is DERIVED from this file's own `stage` calls; there is
#       no second list to drift;
#   §5  every skip is printed BY NAME with a reason, and a skip happens only
#       here, at stage level: a test that skips inside a stage fails it
#       (pytest-stage.sh). --require-all turns skips into failures; an unknown
#       stage name is REFUSED, and so is a selection of no stage at all;
#   §6  a run id of timestamp + pid + commit; per-stage .ok markers; --resume
#       reruns only what has not passed, and REFUSES to cross commits, to run
#       on a dirty tree (two dirty trees of one commit share an id), or to run
#       in another environment (the interpreter, its packages, moth-quantum's checkout, the SHACL engine);
#   §7  an append-only JSONL record of every stage verdict.
#
# USAGE
#   bash verify/run.sh                     every stage
#   bash verify/run.sh --budget quick      the everyday cut: all but study-plants, privacy-controls, instruments,
#                                          p1-crates, p2-crates, p4-shacl
#   bash verify/run.sh --only format,twin  by name (refuses unknown names)
#   bash verify/run.sh --require-all       a skipped stage FAILS the run
#   bash verify/run.sh --list              stages, with * on what would run
#   bash verify/run.sh --resume            continue the most recent run
#
# THERE IS NO CACHE ACROSS RUNS: a fresh invocation runs everything again.
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
STATEROOT="${STATEROOT:-$ROOT/.gate-state}"
export PYTHONIOENCODING=utf-8

ONLY=""; SKIP=""; REQUIRE_ALL=0; LIST=0; RESUME=""; FRESH=0; BUDGET=""

# Named cuts, checked against the derived stage list below.
BUDGET_QUICK=lint,docs,check-docs,vocabulary,tool-tests,vocab-tests,format,custody,p1,p2,p4,profile,control-tests,controls-run,twin,controls,study,privacy

die () { echo "FATAL: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --only)        [ $# -ge 2 ] || die "--only needs a list"; ONLY="$ONLY,$2"; shift 2;;
    --skip)        [ $# -ge 2 ] || die "--skip needs a list"; SKIP="$SKIP,$2"; shift 2;;
    --budget)      [ $# -ge 2 ] || die "--budget needs quick or full"
                   case "$2" in
                     quick) BUDGET=quick; ONLY="$ONLY,$BUDGET_QUICK";;
                     full)  BUDGET=full;;
                     *) die "--budget: unknown budget '$2' (quick, full)";;
                   esac; shift 2;;
    --require-all) REQUIRE_ALL=1; shift;;
    --list)        LIST=1; shift;;
    --resume)      if [ $# -gt 1 ] && [[ ${2:-} != --* ]]; then RESUME=$2; shift 2
                   else RESUME=last; shift; fi;;
    --fresh)       FRESH=1; shift;;
    -h|--help)     awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0;;
    *)             die "unknown option $1";;
  esac
done

in_list() {  # name, comma-list
  case ",$2," in *",$1,"*) return 0;; esac
  return 1
}

SELF="${BASH_SOURCE[0]}"
STAGELIST=$(grep -E '^stage [a-z0-9-]+ "' "$SELF" | awk '{print $2}' | tr '\n' ' ')
STAGELIST="${STAGELIST% }"

check_names() {  # <flagname> <comma-list>
  local n
  for n in $(echo "$2" | tr ',' ' '); do
    [ -z "$n" ] && continue
    case " $STAGELIST " in
      *" $n "*) ;;
      *) echo "ERROR: $1 names unknown stage '$n'" >&2
         echo "       stages: $STAGELIST" >&2
         exit 2;;
    esac
  done
}
check_names --only "$ONLY"
check_names --skip "$SKIP"
# `--only ""` (or an unset variable) selects nothing, and a run of zero
# stages is not a pass: the negative control would not even run (verifier-P0 7a).
if [ -n "$ONLY" ] && [ -z "$(printf '%s' "$ONLY" | tr -d ', ')" ]; then
  die "--only names no stage; a run of zero stages is not a pass"
fi

if [ "$LIST" = 1 ]; then
  while IFS=$'\t' read -r _nm _ds; do
    if [ -z "$ONLY" ] || in_list "$_nm" "$ONLY"; then _mk="*"; else _mk=" "; fi
    printf '%s %-17s %s\n' "$_mk" "$_nm" "$_ds"
  done < <(grep -E '^stage [a-z0-9-]+ "' "$SELF" | sed -E 's/^stage ([a-z0-9-]+) +"([^"]*)".*/\1\t\2/')
  echo
  if [ -n "$ONLY" ]; then
    printf '* = would run%s. Unmarked stages are NOT in this selection.\n' "${BUDGET:+ under --budget $BUDGET}"
  else
    echo "* = would run: every stage (no --only, no --budget)."
  fi
  exit 0
fi

# git runs from inside the tree (the cd above), never with -C "$ROOT": under
# MSYS_NO_PATHCONV=1, which moth-quantum's Atlas work set, git.exe cannot read a /c/... path.
# That once made every run "nogit" and never dirty, so a dirty tree passed
# the --resume guard below (found by the lead, 2026-09-25). A tree with a .git
# that git cannot read is refused rather than called "nogit".
# A tree that is not its own git toplevel (an export copied inside another
# repository) would otherwise be stamped with that repository's commit
# (verifier-P0's re-check, FAILURE-MODES C2): it is "nogit". The test is
# --show-cdup, which is empty exactly at the toplevel, and needs no path
# spelling: comparing two spellings refused every clone under %TEMP%, which
# Git Bash mounts at /tmp (verifier-P0's third pass).
# QRO-Crate's change to the copied framework: a repository git reads, at its
# own toplevel, with no commit yet is "nocommit", and always dirty. Its run id
# names no tree, so --resume refuses it below, as it refuses a dirty one.
if CDUP=$(git rev-parse --show-cdup 2>/dev/null) && [ -z "$CDUP" ] && COMMIT=$(git rev-parse --short HEAD 2>/dev/null); then
  STATUS=$(git status --porcelain) || die "git status failed in $ROOT"
  DIRTY=$([ -n "$STATUS" ] && echo "+dirty" || echo "")
elif [ -n "${CDUP+set}" ] && [ -z "$CDUP" ] && git rev-parse --git-dir >/dev/null 2>&1 &&
     ! git rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
  COMMIT=nocommit; DIRTY="+dirty"
elif [ -e "$ROOT/.git" ]; then
  die "git cannot read the repository at $ROOT; a run id needs its commit"
else
  COMMIT=nogit; DIRTY=""
fi
if [ -n "$RESUME" ] && [ "$FRESH" = 1 ]; then die "--resume and --fresh are contradictory"; fi
if [ -n "$RESUME" ] && [ "$COMMIT" = nogit ]; then die "--resume needs a git tree: without one a run id names no tree"; fi
# A dirty tree has no identity: two different dirty trees of one commit share
# an id, and a resumed run once reported PASSED over a failing authority that
# way (verifier-P0 7b). Resuming is for a committed tree only.
if [ -n "$RESUME" ] && [ -n "$DIRTY" ]; then
  die "--resume refuses a dirty tree: its run id cannot say which tree it was. Commit, or run fresh."
fi
if [ -n "$RESUME" ]; then
  if [ "$RESUME" = last ]; then
    RUNID=$(ls -1 "$STATEROOT" 2>/dev/null | sort | tail -n 1)
    [ -n "$RUNID" ] || die "--resume: no previous run under $STATEROOT"
  else
    RUNID=$RESUME
  fi
  case "$RUNID" in
    *-"$COMMIT$DIRTY") ;;
    *) die "run $RUNID was a different tree than $COMMIT$DIRTY; half a run of one tree glued to half a
  run of another is a report about neither. Use --fresh.";;
  esac
else
  RUNID="$(date +%Y%m%d-%H%M%S)-$$-$COMMIT$DIRTY"
fi
RUNDIR="$STATEROOT/$RUNID"
mkdir -p "$STATEROOT"

# What a stage runs against that is not in the tree: the interpreter and its
# packages, the variables that decide what an import finds, the moth-quantum
# checkout the instruments stage reads (its commit and whether it is clean, never
# its path), and the SHACL engine P4's stage runs (its interpreter's path, and its
# packages). A resumed run once reported a stage passed for an environment that
# failed a fresh run (moth-quantum, verifier-P0's re-check).
#
# An interpreter's packages are each distribution it finds, as name==version, sorted, and hashed. Each is read
# with .get, so that one with no name or version is listed as None==None: the expression once added None to a
# string, and raised TypeError (P0.4's verifier, round 1); indexing a missing key raises KeyError where the
# standard library follows importlib_metadata 8 (round 2); and the runner hashed the traceback, which lists no
# package at all. A listing that fails for any other reason, a METADATA not in UTF-8 say, is no list: its hash is
# made unique, so that --resume refuses the environment, never takes a traceback for one (round 3).
PACKAGES='import importlib.metadata as m; print(sorted("%s==%s" % ((d.metadata or {}).get("Name"), (d.metadata or {}).get("Version")) for d in m.distributions()))'
packages () {                   # packages INTERPRETER [OPTION...]: its packages' hash
  local out
  out=$("$@" -c "$PACKAGES" 2>&1) || out="no list: $(date +%s%N) $$ $RANDOM"
  printf '%s' "$out" | sha256sum | cut -c1-16
}
fingerprint () {
  local moth=absent
  if [ -n "${QRO_MOTH_ROOT:-}" ]; then
    moth=$( (cd "$QRO_MOTH_ROOT" && git --no-optional-locks rev-parse --short HEAD &&
             git --no-optional-locks status --porcelain | wc -l) 2>&1 | tr '\n' ' ')
  fi
  echo "python=$(python -c 'import sys; print(sys.version.split()[0])' 2>&1)"
  echo "tools=$(python -m ruff --version 2>&1) / $(python -m pytest --version 2>&1 | head -1)"
  echo "packages=$(packages python)"
  echo "import-path=PYTHONPATH:${PYTHONPATH:-} PYTHONSAFEPATH:${PYTHONSAFEPATH:-} PYTHONHOME:${PYTHONHOME:-}"
  echo "machine=$(python -c 'import platform; print(platform.platform(), platform.machine())' 2>&1)"
  echo "moth-quantum=$moth"
  echo "shacl-engine=$(shacl_engine)"
}

# The SHACL engine of P4's p4-shacl stage, by its interpreter and the packages it holds, read isolated (-I), so
# that no variable of the runner's moves what it finds; and so that a run resumed under another engine is not
# taken for this one's (P0.3's verifier, round 1).
shacl_engine () {
  if [ -z "${QRO_SHACL_PYTHON:-}" ]; then echo absent; return; fi
  echo "$QRO_SHACL_PYTHON $(packages "$QRO_SHACL_PYTHON" -I)"
}
if [ -z "$RESUME" ]; then
  # Two fresh runs in one second once shared a directory, and the second read
  # the first's .ok markers (verifier-P0 7c). The pid separates them, and a
  # fresh run that finds its directory already there refuses.
  mkdir "$RUNDIR" 2>/dev/null || die "run directory $RUNDIR already exists; a fresh run never reuses markers"
  fingerprint > "$RUNDIR/environment"
else
  [ -d "$RUNDIR" ] || die "--resume: there is no run $RUNID under $STATEROOT"
  [ "$(fingerprint)" = "$(cat "$RUNDIR/environment" 2>/dev/null)" ] || die "--resume: this environment is not
  the run's (python and its packages, the import path, moth-quantum's checkout, or the SHACL engine); see $RUNDIR/environment. Use --fresh."
fi
JSONL="$RUNDIR/stages.jsonl"

PASSED=0; FAILED=0; SKIPPED=0; CACHED=0
note () { echo "   $*"; }

echo "== run $RUNID"
echo "   commit $COMMIT$DIRTY, python $(python -c 'import sys; print(sys.version.split()[0])' 2>/dev/null || echo '?'), state in $RUNDIR"
[ -n "$BUDGET" ] && echo "   budget $BUDGET"

# stage <name> <description> -- command...
# MUST_FAIL=1 before a stage inverts its verdict: the command must fail.
# MUST_SAY="text" with it: and its log must say why. A control that fails for
# some other reason (a crash, a command line that refuses everything) proves
# nothing about the fault it plants.
stage() {
  local name=$1 desc=$2; shift 3
  local t0 t1 rc verdict="" reason="" expect_fail="${MUST_FAIL:-0}" must_say="${MUST_SAY:-}"
  MUST_FAIL=0; MUST_SAY=""
  if [ -n "$ONLY" ] && ! in_list "$name" "$ONLY"; then
    STAGE_SKIP_REASON=""
    return 0
  fi
  if [ -f "$RUNDIR/$name.ok" ]; then
    CACHED=$((CACHED+1))
    note "$(printf '%-17s %-7s %s' "$name" "ok" "(passed earlier in this run)")"
    echo "{\"stage\":\"$name\",\"verdict\":\"ok-cached\"}" >> "$JSONL"
    STAGE_SKIP_REASON=""
    return 0
  fi
  if in_list "$name" "$SKIP"; then
    verdict=SKIP; reason="requested"
  elif [ -n "${STAGE_SKIP_REASON:-}" ]; then
    verdict=SKIP; reason=$STAGE_SKIP_REASON
  fi
  if [ "$verdict" = SKIP ]; then
    SKIPPED=$((SKIPPED+1))
    note "$(printf '%-17s %-7s %s' "$name" "SKIP" "$reason")"
    echo "{\"stage\":\"$name\",\"verdict\":\"skip\",\"reason\":\"$reason\"}" >> "$JSONL"
    [ "$REQUIRE_ALL" = 1 ] && FAILED=$((FAILED+1))
    STAGE_SKIP_REASON=""
    return 0
  fi
  t0=$(date +%s)
  "$@" > "$RUNDIR/$name.log" 2>&1
  rc=$?
  t1=$(date +%s)
  if [ "$expect_fail" = 1 ]; then
    if [ "$rc" -eq 0 ]; then
      FAILED=$((FAILED+1))
      note "$(printf '%-17s %-7s %s' "$name" "FAIL" "NEGATIVE CONTROL DID NOT FAIL - this runner cannot detect a defect")"
      echo "{\"stage\":\"$name\",\"verdict\":\"control-passed\"}" >> "$JSONL"
      return 1
    fi
    if [ -n "$must_say" ] && ! grep -qF -- "$must_say" "$RUNDIR/$name.log"; then
      : > "$RUNDIR/$name.fail"
      FAILED=$((FAILED+1))
      note "$(printf '%-17s %-7s %s' "$name" "FAIL" "the control failed, but not with \"$must_say\"; see $RUNDIR/$name.log")"
      echo "{\"stage\":\"$name\",\"verdict\":\"control-wrong-reason\",\"rc\":$rc}" >> "$JSONL"
      return 1
    fi
    rc=0
    note "$(printf '%-17s %-7s %s' "$name" "ok" "(the negative control failed, as it must: $desc)")"
  fi
  if [ "$rc" -eq 0 ]; then
    : > "$RUNDIR/$name.ok"
    PASSED=$((PASSED+1))
    [ "$expect_fail" = 1 ] || note "$(printf '%-17s %-7s %3ss  %s' "$name" "ok" "$((t1-t0))" "$desc")"
    echo "{\"stage\":\"$name\",\"verdict\":\"ok\",\"seconds\":$((t1-t0))}" >> "$JSONL"
  else
    : > "$RUNDIR/$name.fail"
    FAILED=$((FAILED+1))
    note "$(printf '%-17s %-7s rc=%s  see %s' "$name" "FAIL" "$rc" "$RUNDIR/$name.log")"
    echo "{\"stage\":\"$name\",\"verdict\":\"fail\",\"rc\":$rc}" >> "$JSONL"
  fi
}

# Set a skip reason for the NEXT stage when what it needs is absent. A
# missing tool must never look like a pass. The command guard moth-quantum's
# runner has, `need`, is gone: nothing called it, and no rule read a call of
# it (P0.4's verifier, round 3).
need_file () { [ -e "$1" ] || STAGE_SKIP_REASON="$2"; }
need_env ()  { [ -n "${!1:-}" ] || STAGE_SKIP_REASON="$2"; }

# ======================================================================
# THE STAGES. One `stage` line each, the description in double quotes on
# the same line, so the list above is derived from them. A pytest stage runs
# a DIRECTORY, so a new test file joins its stage by where it is saved, and
# tests/docs/test_stage_registry.py fails any test file that no stage runs.
# ======================================================================

stage lint "ruff over the package, the controls, the tools and the tests" -- \
  python -m ruff check qro controls tools tests

stage docs "the registry, from the runner's text: each test file and tool check run by a stage; no two test files share a name, and a parcel's carry its prefix; pytest's configuration pinned to pyproject.toml" -- \
  bash verify/pytest-stage.sh tests/docs

stage check-docs "the documents' own gate, on what it reads: links resolve, the index lists the documents, named paths exist" -- \
  python tools/check_docs.py

stage vocabulary "the context, the vocabulary, the refusal list and the control list regenerate byte for byte" -- \
  python tools/gen_vocabulary.py --check

stage tool-tests "the tools' own checks watched to fail: the vocabulary's drift, a wrong checkout, every privacy alternative" -- \
  bash verify/pytest-stage.sh tests/tools

stage vocab-tests "the table passes its sanity check; RO-Crate's context is the pinned copy; each refusal name the code spells is a row" -- \
  bash verify/pytest-stage.sh tests/vocabulary

stage format "the spellings; the canonical writer; every P0 refusal planted, and refused by its own name" -- \
  bash verify/pytest-stage.sh tests/format

stage custody "the custody log's chain and head, the audit record, the appended withdrawal, the stated limits" -- \
  bash verify/pytest-stage.sh tests/custody

# The parcels' stages, written by the lead before the parcels build, so that parcels building at once never edit
# this file (P0.1's verifier, round 1, D3). Each runs its parcel's own directory, and skips by name until that
# directory exists. P3's and P5's are written when their briefs go out; a parcel that needs another stage asks.
need_file tests/p1 "P1, the adapter, is not built yet: there is no tests/p1"
stage p1 "P1, the adapter: Quantum-Film's records and IBM's into crates; checker steps 4, 5 and 8" -- \
  bash verify/pytest-stage.sh tests/p1

need_file tests/p2 "P2, the golden measures, is not built yet: there is no tests/p2"
stage p2 "P2, the golden measures: measures, twins, floor, certified intervals, the exact hold; steps 6 and 7" -- \
  bash verify/pytest-stage.sh tests/p2

need_file tests/p4 "P4, the profile, is not built yet: there is no tests/p4"
stage p4 "P4, the profile: the Profile Crate, the context, the shapes and the examples" -- \
  bash verify/pytest-stage.sh tests/p4

# P1's second stage (its design, approved 2026-10-15): its two crates built from moth-quantum's records, so
# out of the quick budget, and skipped by name without moth-quantum or before the directory exists.
need_env QRO_MOTH_ROOT "moth-quantum's checkout is not named (QRO_MOTH_ROOT, clean at 3a73823)"
need_file tests/p1crates "P1's crates are not built yet: there is no tests/p1crates"
stage p1-crates "P1's two crates built from moth-quantum's records and accepted; the controls and sweeps on the real IBM crate" -- \
  bash verify/pytest-stage.sh tests/p1crates

# P2's second stage (its design, approved 2026-10-15): v0's two crates' measures, intervals and exact holds, so
# out of the quick budget, as P1's is.
need_env QRO_MOTH_ROOT "moth-quantum's checkout is not named (QRO_MOTH_ROOT, clean at 3a73823)"
need_file tests/p2crates "P2's crate-level tests are not built yet: there is no tests/p2crates"
stage p2-crates "P2 on v0's two crates: every gate list held, the measures and section 6.1's intervals reproduced" -- \
  bash verify/pytest-stage.sh tests/p2crates

# P4's generator, and its engine's stage (its design, approved 2026-10-15). The generated profile is checked in
# the quick budget once the tool exists. The engine's stage needs a SHACL engine outside the tree, named by
# QRO_SHACL_PYTHON, which only Logan allows, so it is out of the quick budget.
need_file tools/gen_profile.py "P4's generator is not built yet: there is no tools/gen_profile.py"
stage profile "the profile's generated files regenerate byte for byte; the Profile Crate holds what RO-Crate 1.3 asks" -- \
  python tools/gen_profile.py --check

need_env QRO_SHACL_PYTHON "no SHACL engine is named (QRO_SHACL_PYTHON: a Python with pyshacl 0.40.1, outside the tree)"
need_file tests/p4shacl "P4's engine stage is not built yet: there is no tests/p4shacl"
stage p4-shacl "a SHACL engine reads P4's shapes and judges each example as the evaluator does" -- \
  bash verify/pytest-stage.sh tests/p4shacl

stage control-tests "the controls' registry walked both ways; each built control comes out as section 11 says" -- \
  bash verify/pytest-stage.sh tests/controls

stage controls-run "every built control of section 11 through the registry; every other printed as pending" -- \
  python -m controls.run

# The control and its twin, through QRO-Crate's own command line: a command
# line that refused everything would otherwise pass the control.
stage twin "the fixture crate, every control's twin, accepted by QRO-Crate's own command line" -- \
  python -m controls.plant twin

# The control must FAIL, and name its refusal: a shot moved under a digest left
# as it was. If this passes, a moved shot would go unnoticed.
MUST_FAIL=1 MUST_SAY="REFUSED raw-digest"
stage controls "a shot moved under its digest MUST be refused by QRO-Crate's own command line, as raw-digest" -- \
  python -m controls.plant shot-moved

stage study "study QRO-0's own gate: draft numbers, tables, section references, instrument hashes" -- \
  python -I docs/studies/qro0/check_study.py docs/studies/QRO-0.md

stage study-plants "the study's gate, held to the failure each planted fault targets" -- \
  python -I docs/studies/qro0/check_study_plants.py docs/studies/QRO-0.md

stage privacy "none of the gate's shapes of home path, address or key in a file git would commit, a blob of an earlier commit, or a commit message" -- \
  python tools/check_privacy.py

stage privacy-controls "the privacy gate catches each planted path, address and key" -- \
  python tools/check_privacy.py --control

need_env QRO_MOTH_ROOT "moth-quantum's checkout is not named (QRO_MOTH_ROOT, clean at 3a73823)"
stage instruments "the study's five analysis instruments reproduce their kept outputs byte for byte" -- \
  python tools/check_instruments.py "${QRO_MOTH_ROOT:-}"

# ======================================================================

echo "== summary"
echo "   passed $PASSED, failed $FAILED, skipped $SKIPPED, cached $CACHED"
echo "   record $JSONL"
if [ $((PASSED + FAILED + CACHED)) -eq 0 ]; then
  echo "== FAILED: no stage ran (a skip is not a run)"
  exit 1
fi
if [ -n "$ONLY" ] && ! in_list controls "$ONLY"; then
  echo "   (the negative control was not in this selection)"
fi
if [ "$FAILED" -ne 0 ]; then
  echo "== FAILED"
  exit 1
fi
if [ "$SKIPPED" -ne 0 ] && [ "$REQUIRE_ALL" != 1 ]; then
  echo "== PASSED, with $SKIPPED skipped by name above"
  echo "   (--require-all makes a skip a failure)"
  exit 0
fi
echo "== PASSED"
exit 0
