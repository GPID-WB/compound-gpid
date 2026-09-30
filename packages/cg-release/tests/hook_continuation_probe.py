"""Inject revocation after a real append; retain byte-exact transaction prefixes."""

import json


def revoke_after(journal, roles, actor, predicate):
    """Wrap only append I/O; return observations for the continuing operation."""
    append = journal.store.append
    probe = dict(prefix=list(journal.store.history()[1]), appends=[], revoked=False)

    def delayed(parent, raw, record):
        result = append(parent, raw, record)
        event = json.loads(raw)
        probe["appends"].append(event)
        if actor is not None and not probe["revoked"] and predicate(event):
            roles[actor] = "read"
            probe["revoked"] = True
        return result

    journal.store.append = delayed
    return probe


def assert_prefix(journal, probe):
    assert journal.store.history()[1][: len(probe["prefix"])] == probe["prefix"]
