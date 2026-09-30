"""Signed GitHub App journal commits with atomic expected-head branch updates."""

import base64
import re

from cg_release.events import ControllerError
from cg_release.git_journal import blob_id, transaction_files
from cg_release.github import GitHubReads, decode_json
from cg_release.journal_models import Record, Transaction
from cg_release.journal_transport import encode_files
from cg_release.journal_tree import JournalTree
from cg_release.models import Policy, canonical_bytes, load_record
from cg_release.verification import verification_guard


class GitHubJournalStore:
    """Read exact signed history; GraphQL writes are non-force atomic CAS updates."""

    def __init__(
        self, api: GitHubReads, policy: Policy, *, bot_id: int, writable: bool = False
    ) -> None:
        """Bind reviewed root; use bot_id from verified control checks."""
        self.api, self.policy, self.bot_id, self.writable = (
            api,
            policy,
            bot_id,
            writable,
        )
        self.writer = f"app:{policy.apps.control}"

    def head(self) -> str:
        """Read the current state branch SHA, e.g. store.head()."""
        return self.api.branch(self.policy.state_branch)["commit"]["sha"]

    def _tree(self, commit: dict) -> dict[str, str]:
        oid = commit["commit"]["tree"]["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise ValueError
        value = self.api._request(
            f"repos/{self.api.slug}/git/trees/{oid}?recursive=1", None
        )
        if value["sha"] != oid or value["truncated"] is not False:
            raise ValueError
        paths = {}
        for item in value["tree"]:
            if item["type"] == "tree" and item["mode"] == "040000":
                continue
            path = item["path"]
            if (
                item["type"] != "blob"
                or item["mode"] != "100644"
                or path in paths
                or not re.fullmatch(
                    r"(?:events/[0-9]{10,}|(?:requests|reservations|recoveries|compositions)/[0-9a-f]{64}|queue)\.json",
                    path,
                )
            ):
                raise ValueError
            paths[path] = item["sha"]
        return paths

    def _blob(self, oid: str) -> bytes:
        value = self.api.get("git/blobs/" + oid)
        if (
            value["sha"] != oid
            or value["encoding"] != "base64"
            or type(value["size"]) is not int
            or not 0 <= value["size"] <= 65536
        ):
            raise ValueError
        raw = base64.b64decode(value["content"].replace("\n", ""), validate=True)
        if len(raw) != value["size"] or blob_id(raw) != oid:
            raise ValueError
        return raw

    def history(self) -> tuple[str, list[Transaction]]:
        """Verify the root, signed control commits, event chain, and derived tree.

        Returns bounded chronological transactions, e.g. store.history().
        Raises ControllerError instead of treating absent/corrupt history as empty.
        """
        try:
            check = verification_guard(self)
            current, backwards, seen = self.head(), [], set()
            while current != self.policy.journal_root:
                check()
                if current in seen or not re.fullmatch(r"[0-9a-f]{40}", current):
                    raise ValueError
                seen.add(current)
                commit = self.api.get("commits/" + current)
                verification = commit["commit"]["verification"]
                if (
                    commit["sha"] != current
                    or len(commit["parents"]) != 1
                    or verification["verified"] is not True
                    or verification["reason"] != "valid"
                    or not verification["signature"]
                    or not verification["payload"]
                    or type(commit["committer"]["id"]) is not int
                    or commit["committer"]["id"] != self.bot_id
                ):
                    raise ValueError
                backwards.append(commit)
                current = commit["parents"][0]["sha"]
            root = self.api.get("commits/" + self.policy.journal_root)
            expected = JournalTree()
            if (
                root["sha"] != self.policy.journal_root
                or root["parents"]
                or root["commit"]["tree"]["sha"] != expected.oid
                or self._tree(root)
            ):
                raise ValueError
            inventory = self._tree(backwards[0]) if backwards else {}
            transactions = []
            for revision, commit in enumerate(reversed(backwards), 1):
                check()
                event = self._blob(inventory[f"events/{revision:010d}.json"])
                decoded = decode_json(event.decode())
                from cg_release.recovery_models import event_model

                model = event_model(decoded["record"])
                record = load_record(model, canonical_bytes(decoded["record"]))
                if (
                    expected.update(transaction_files(event, record))
                    != commit["commit"]["tree"]["sha"]
                ):
                    raise ValueError
                transactions.append(
                    Transaction(
                        commit["sha"], commit["parents"][0]["sha"], self.writer, event
                    )
                )
            if expected.paths != inventory:
                raise ValueError
            self.last_reconstruction_work = {
                "entry_updates": expected.entry_updates,
                "hash_bytes": expected.hash_bytes,
            }
            return self.policy.journal_root, transactions
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ControllerError(
                "E_JOURNAL",
                "Remote journal root, signature, writer, or atomic tree is invalid.",
            ) from None

    def write_files(
        self, parent: str, files: dict[str, bytes | None], message: str
    ) -> None:
        """Write exact files against expected head, e.g. write_files(head, files, name).

        GraphQL creates GitHub-signed commits without caller-supplied author fields.
        Every result still requires signed-tree read-back by the journal caller.
        """
        if not self.writable or not re.fullmatch(r"[0-9a-f]{40}", parent):
            raise ControllerError(
                "E_AUTHORITY", "Journal writes require trusted controller context."
            )
        payload = encode_files(
            self.api.slug, self.policy.state_branch, parent, files, message
        )
        result = self.api.runner(
            "gh",
            [
                "api",
                "--method",
                "POST",
                "--hostname",
                self.api.host,
                "--include",
                "--input",
                "-",
                "graphql",
            ],
            cwd=self.api.cwd,
            timeout=min(self.api.read_seconds, self.api.remaining()),
            allow_failure=True,
            input_text=payload,
        )
        raw = result.stdout.replace("\r\n", "\n")
        header, separator, body = raw.partition("\n\n")
        if (
            result.returncode
            or not separator
            or not re.match(r"HTTP/[0-9.]+ 200(?: |\n)", header + "\n")
        ):
            raise ControllerError(
                "E_WRITE_UNKNOWN", "Journal write requires read-back reconciliation."
            )
        value = decode_json(body)
        if not isinstance(value, dict) or value.get("errors"):
            code = "E_CAS" if self.head() != parent else "E_WRITE_UNKNOWN"
            raise ControllerError(
                code, "Journal mutation did not return verified success."
            )

    def append(self, parent: str, event: bytes, record: Record) -> None:
        """Atomically append event/request/reservation, e.g. called by Journal.admit."""
        self.write_files(
            parent, transaction_files(event, record), "Release controller checkpoint"
        )
