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

P3's and P5's rows need three things of the runner (P0.10; controls/registry.py's docstring says the protocol):
  - a plant that raises `Refused` makes that refusal the outcome, judged by its name as any other;
  - a plant that returns a `Compared` has the comparison check's outcome (qro.__main__.compare), so while P3's
    module is missing it is `step-unbuilt`, as the command's is;
  - a `states` row is met ("states") when its sentence is in its plant's STATEMENTS set and its TWINS entry's crate
    is accepted without saying it. A built `states` row lacking either entry is pending, never WRONG.
"""
import sys
import tempfile

from controls import registry
from controls.registry import CONTROL, CONTROLS, Compared, plants, sentence
from qro import checker, custody, fixture
from qro.__main__ import compare, escape
from qro.refusal import Refused


def hold(planted):
    """Raise Refused unless the check of what was planted accepts it: a comparison by the comparison check, a custody
    pair by the custody check, a crate by the checker. A Compared is a tuple, so it is told first."""
    if isinstance(planted, Compared):
        compare(planted.comparison_dir, planted.crate_dirs)
    elif isinstance(planted, tuple):
        log, rec = planted
        custody.check_log(log)
        if rec is not None:
            custody.check_record(rec, log)
    else:
        checker.check(planted)


def said(statements, name, planted):
    """The sentences row `name`'s STATEMENTS entry says of `planted`: a set, never a string (a string would be read
    as the characters it holds)."""
    got = statements[name](planted)
    if not isinstance(got, (set, frozenset)):
        raise TypeError(f"the STATEMENTS entry of {name} returned a {type(got).__name__}, not a set of sentences")
    return got


def pending_reason(c, every, statements, twins):
    """Why a built row is still pending, or None. A `states` row needs its STATEMENTS entry and its TWINS entry: with
    either missing nothing shows that the plant says the sentence and the twin does not."""
    if c.name not in every or c.expected != "states":
        return None
    if c.name not in statements:
        return "its plants module has no STATEMENTS entry for it"
    if c.name not in twins:
        return "its plants module has no TWINS entry for it"
    return None


def states(c, planted, statements, twins):
    """The outcome of a `states` row whose plant the check accepted."""
    want = sentence(c)
    if want is None:
        return "accepted", None, "the row's text quotes no sentence"
    if want not in said(statements, c.name, planted):
        return "accepted", None, f"its plant does not say {want!r}"
    with tempfile.TemporaryDirectory() as d:
        twin = twins[c.name](d)
        try:
            hold(twin)
        except Refused as r:
            return "twin-refused", r.name, f"{r.where}: {r.detail}"
        if want in said(statements, c.name, twin):
            return "twin-states", None, f"its twin says {want!r} too"
    return "states", None, ""


def outcome(name, every=None, statements=None, twins=None):
    """("accepted", None, "") or ("refused", refusal name, where), for the control's planted fault; a `states` row
    that is met is ("states", None, ""). A `Refused` the plant itself raises is the plant's outcome."""
    every = plants() if every is None else every
    fixture.register()
    checker.load()
    c = CONTROL.get(name)
    try:
        with tempfile.TemporaryDirectory() as d:
            planted = every[name](d)
            hold(planted)
            if c is None or c.expected != "states":
                return "accepted", None, ""
            statements = registry.statements() if statements is None else statements
            twins = registry.twins() if twins is None else twins
            if name not in statements or name not in twins:
                return "pending", None, "its plants module gives no STATEMENTS or no TWINS entry for it"
            return states(c, planted, statements, twins)
    except Refused as r:
        return "refused", r.name, f"{r.where}: {r.detail}"


def say(line):
    print(escape(line))


def main(every=None, statements=None, twins=None):
    every = plants() if every is None else every
    statements = registry.statements() if statements is None else statements
    twins = registry.twins() if twins is None else twins
    bad = built = 0
    for c in CONTROLS:
        reason = pending_reason(c, every, statements, twins)
        if c.name not in every:
            if c.owner == "P0":                              # P0's are built, or this run fails by name
                bad += 1
                say(f"WRONG     {c.name:22} P0's control, with no plant")
            else:
                say(f"pending   {c.name:22} {c.owner}: {c.text}")
            continue
        if reason is not None:
            say(f"pending   {c.name:22} {c.owner}: {c.text} ({reason})")
            continue
        built += 1
        if c.expected == "states":
            got, name, where = outcome(c.name, every, statements=statements, twins=twins)
        else:
            got, name, where = outcome(c.name, every)
        ok = (got, name) == (c.expected, c.refusal)
        bad += not ok
        say(f"{'ok' if ok else 'WRONG':9} {c.name:22} {got}{' ' + name if name else ''}"
              f"{' at ' + where if where else ''}" + ("" if ok else f"; section 11 says {c.text}"))
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
