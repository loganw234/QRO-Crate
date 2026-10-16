"""Run every built control, from the command line: each planted fault must come out as section 11 says.

    python -m controls.run        # 0 = every built control did; 1 = each one that did not, by name; 3 = the run
                                  # itself failed, a parcel's module that would not load among the causes

It prints each control's outcome, and every pending row (another parcel's, not yet built) by name. A control
counts only if it is refused by the name its row gives, or accepted where its row says accepted; a refusal by
any other name is a failure, since it proves nothing about the fault it plants (moth-quantum, verify/run.sh's
MUST_SAY). A row of P0's with no plant fails the run by name. The checker runs as the command line runs it: the
fixture's raw form and generator registered, and every parcel's steps (checker.load). Each line is printable
ASCII, written as the command line writes its own (qro.__main__.escape): a crate's or a module's text, echoed,
neither breaks a line nor fails to print (P0.1's verifier, round 4, N3). Stdlib only.
"""
import sys
import tempfile

from controls.registry import CONTROLS, plants
from qro import checker, custody, fixture
from qro.__main__ import escape
from qro.refusal import Refused


def outcome(name, every=None):
    """("accepted", None, "") or ("refused", refusal name, where), for the control's planted fault."""
    every = plants() if every is None else every
    fixture.register()
    checker.load()
    with tempfile.TemporaryDirectory() as d:
        planted = every[name](d)
        try:
            if isinstance(planted, tuple):
                log, rec = planted
                custody.check_log(log)
                if rec is not None:
                    custody.check_record(rec, log)
            else:
                checker.check(planted)
        except Refused as r:
            return "refused", r.name, f"{r.where}: {r.detail}"
    return "accepted", None, ""


def say(line):
    print(escape(line))


def main(every=None):
    every = plants() if every is None else every
    bad = 0
    for c in CONTROLS:
        if c.name not in every:
            if c.owner == "P0":                              # P0's are built, or this run fails by name
                bad += 1
                say(f"WRONG     {c.name:22} P0's control, with no plant")
            else:
                say(f"pending   {c.name:22} {c.owner}: {c.text}")
            continue
        got, name, where = outcome(c.name, every)
        ok = (got, name) == (c.expected, c.refusal)
        bad += not ok
        say(f"{'ok' if ok else 'WRONG':9} {c.name:22} {got}{' ' + name if name else ''}"
              f"{' at ' + where if where else ''}" + ("" if ok else f"; section 11 says {c.text}"))
    built = sum(c.name in every for c in CONTROLS)
    say(f"{built - bad} of {built} built controls came out as section 11 says; "
          f"{len(CONTROLS) - built} pending other parcels")
    return 1 if bad else 0


def run():
    """main(), with the run's own failure as exit 3 and its one line, never a pass: a parcel's module that raised
    SystemExit(0) while it loaded ended the run with exit 0 and no output (P0.1's verifier, round 3, note 1)."""
    try:
        return main()
    except BaseException as x:
        say(f"FAILED: the controls' run itself failed, {checker.describe(x)}; this is not a verdict on the controls")
        return 3


if __name__ == "__main__":
    sys.exit(run())
