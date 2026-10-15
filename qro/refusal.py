"""A refusal by name and location: the only alternative to an accepted crate (HonestFramework, METHOD.md section 2).

Every name raised is a row of qro/vocabulary.py's REFUSALS, so the refusal list cannot drift from what the code
raises.
"""
from qro import vocabulary as V


class Refused(Exception):
    def __init__(self, name, where, detail):
        if name not in V.REFUSAL:
            raise KeyError(f"{name} is not a refusal in qro/vocabulary.py")
        super().__init__(f"{name} at {where}: {detail}")
        self.name, self.where, self.detail = name, where, detail
