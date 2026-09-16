"""Fault-injected test store; not a production persistence or authority provider."""

import hashlib
import json

from cg_release.events import ControllerError
from cg_release.journal_models import Transaction


class MemoryStore:
    writer = "control-app"

    def __init__(self):
        self.transactions = []
        self.revision = 0
        self.before_write = None
        self.lose_response = False

    def history(self):
        return "a" * 40, list(self.transactions)

    def append(self, parent, event, record):
        if self.before_write is not None:
            callback, self.before_write = self.before_write, None
            callback()
        actual = self.transactions[-1].commit if self.transactions else "a" * 40
        if parent != actual:
            raise ControllerError("E_CAS", "Competing sibling update.")
        commit = hashlib.sha1(parent.encode() + event).hexdigest()
        self.transactions.append(Transaction(commit, parent, self.writer, event))
        self.revision += 1
        if self.lose_response:
            self.lose_response = False
            raise ControllerError("E_TIMEOUT", "Response lost after acceptance.")

    def corrupt(self, kind):
        transaction = self.transactions[-1]
        event = json.loads(transaction.event)
        parent, writer = transaction.parent, transaction.writer
        if kind == "writer":
            writer = "intruder"
        elif kind == "parent":
            parent = "b" * 40
        elif kind == "record":
            event["record"]["state"] = "complete"
        elif kind == "reservation":
            event["record"]["request"]["version"] = "9.0.0"
        else:
            event["previous"] = "f" * 64
        self.transactions[-1] = Transaction(
            transaction.commit, parent, writer, json.dumps(event).encode()
        )
