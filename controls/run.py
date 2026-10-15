"""Run every built control, from the command line: each planted fault must come out as section 11 says.

    python -m controls.run        # 0 = every built control did; 1 = each one that did not, by name

It prints each control's outcome, and every pending row (another parcel's, not yet built) by name. A control
counts only if it is refused by the name its row gives, or accepted where its row says accepted; a refusal by
any other name is a failure, since it proves nothing about the fault it plants (moth-quantum, verify/run.sh's
MUST_SAY). Stdlib only.
"""
import sys
import tempfile

from controls.registry import CONTROLS, PLANTS
from qro import checker, custody, fixture
from qro.refusal import Refused


def outcome(name):
    """("accepted", None) or ("refused", refusal name), for the control's planted fault."""
    fixture.register()
    with tempfile.TemporaryDirectory() as d:
        planted = PLANTS[name](d)
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


def main():
    bad = 0
    for c in CONTROLS:
        if c.name not in PLANTS:
            if c.owner == "P0":                              # P0's are built, or this run fails by name
                bad += 1
                print(f"WRONG     {c.name:22} P0's control, with no plant")
            else:
                print(f"pending   {c.name:22} {c.owner}: {c.text}")
            continue
        got, name, where = outcome(c.name)
        ok = (got, name) == (c.expected, c.refusal)
        bad += not ok
        print(f"{'ok' if ok else 'WRONG':9} {c.name:22} {got}{' ' + name if name else ''}"
              f"{' at ' + where if where else ''}" + ("" if ok else f"; section 11 says {c.text}"))
    built = sum(c.name in PLANTS for c in CONTROLS)
    print(f"{built - bad} of {built} built controls came out as section 11 says; "
          f"{len(CONTROLS) - built} pending other parcels")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
