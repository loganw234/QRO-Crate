"""Helpers for P5.1's tests: the network gate every module lists in its `pytestmark`, the unit twin (built once in the process
and copied for each test that writes), and the generator run with its guard named. It names no function `test*` and no class
`Test*`.

The network gate (design item 6): an autouse fixture that makes `socket.socket.connect` and `socket.getaddrinfo` raise, so
that no test of P5 reaches a network, the stand-in service's tests among them. No conftest.py is allowed, so each module
imports the fixture and lists it in `pytestmark`.
"""
import socket
from pathlib import Path

import pytest

from controls import plants_p5
from qro import p1_guards, p5_generate

ROOT = Path(__file__).resolve().parents[2]


class NetworkRefused(AssertionError):
    """A test of P5 tried to reach the network."""


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise NetworkRefused("P5's tests reach no network")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


@pytest.fixture(autouse=True)
def no_link_left_behind(tmp_path):
    """CLAUDE.md item 10: a test that makes a junction removes it; one left in tmp_path fails the test."""
    yield
    left = [p.name for p in Path(tmp_path).rglob("*") if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())]
    assert not left, f"a link was left behind: {left}"


def twin(tmp_path, **options):
    """A fresh copy of the built twin (options as controls.plants_p5.build_unit takes them) in tmp_path/crate."""
    return plants_p5.copy_of(tmp_path, **options)


def forge(crate):
    return plants_p5.Forge(crate)


def guard(crate):
    """The GuardError the unit generator raises on the crate, or None."""
    try:
        p5_generate.unit(crate)
    except p1_guards.GuardError as g:
        return g
    return None


def letter(crate):
    """The guard's letter that refuses the crate, or None where the generator accepts it."""
    g = guard(crate)
    return None if g is None else g.guard
