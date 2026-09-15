"""Local bare-Git journal backend for offline atomicity and recovery verification.

This backend is deliberately not a GitHub authority adapter. Commit author text
does not prove App identity; remote use requires verified App/ruleset controls.
"""

import hashlib
import re
from pathlib import Path

from cg_release.events import ControllerError
from cg_release.github import decode_json
from cg_release.journal_models import Record, Transaction
from cg_release.models import canonical_bytes
from cg_release.policy import safe_ref
from cg_release.process import run_process
from cg_release.verification import verification_guard


def blob_id(raw: bytes) -> str:
    """Return the Git blob identity, e.g. blob_id(b'{}'), without object writes."""
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def transaction_files(event: bytes, record: Record) -> dict[str, bytes | None]:
    """Build the atomic event/request/reservation set, e.g. for a store append."""
    value = decode_json(event.decode("utf-8"))
    if (
        not isinstance(value, dict)
        or type(value.get("revision")) is not int
        or value["revision"] < 1
    ):
        raise ControllerError("E_JOURNAL", "Journal event revision is invalid.")
    from cg_release.composition_journal import Composition
    from cg_release.queue import QueueCursor
    from cg_release.recovery_models import RecoveryAudit

    if isinstance(record, Composition):
        return {
            f"events/{value['revision']:010d}.json": event,
            f"compositions/{record.key}.json": canonical_bytes(record),
        }
    if isinstance(record, RecoveryAudit):
        return {
            f"events/{value['revision']:010d}.json": event,
            f"recoveries/{record.directive_digest}.json": canonical_bytes(record),
        }
    if isinstance(record, QueueCursor):
        return {
            f"events/{value['revision']:010d}.json": event,
            "queue.json": canonical_bytes(record),
        }
    request_key = hashlib.sha256(record.request_id.encode()).hexdigest()
    version_key = hashlib.sha256(
        record.request.version.split("+")[0].encode()
    ).hexdigest()
    return {
        f"events/{value['revision']:010d}.json": event,
        f"requests/{request_key}.json": canonical_bytes(record),
        f"reservations/{version_key}.json": None
        if record.state == "abandoned"
        else canonical_bytes(
            {
                "request_id": record.request_id,
                "version": record.request.version.split("+")[0],
            }
        ),
    }


class LocalGitStore:
    """Atomic compare-and-swap on a local bare repository, never the user checkout."""

    def __init__(
        self, directory: Path, branch: str, *, anchor: str, writer: str
    ) -> None:
        """Bind an explicit offline bootstrap, e.g. LocalGitStore(bare, branch, ...).

        Args: directory is an existing bare repository; branch is the state ref;
            anchor is its reviewed root commit; writer is the fixture author.
        Raises: ControllerError on malformed identity or a non-bare repository.
        """
        safe_ref(branch)
        identity = re.fullmatch(
            r"([A-Za-z0-9 ._-]+) <([A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+)>", writer
        )
        if not re.fullmatch(r"[0-9a-f]{40}", anchor) or identity is None:
            raise ControllerError(
                "E_JOURNAL", "Explicit journal anchor/writer is required."
            )
        self.directory, self.branch, self.anchor, self.writer = (
            directory,
            branch,
            anchor,
            writer,
        )
        self.name, self.email = identity[1], identity[2]
        if self._git(["rev-parse", "--is-bare-repository"]).stdout.strip() != "true":
            raise ControllerError(
                "E_JOURNAL",
                "Local journal backend requires an isolated bare repository.",
            )

    def _git(
        self, args: list[str], *, text: str | None = None, allow_failure: bool = False
    ):
        guard = getattr(self, "_guard", None)
        return run_process(
            "git",
            args,
            cwd=self.directory,
            input_text=text,
            allow_failure=allow_failure,
            **({"timeout": min(20, guard())} if guard else {}),
        )

    def _tree(self, commit: str) -> dict[str, str]:
        output = self._git(["ls-tree", "-r", "-z", commit]).stdout
        result = {}
        for line in output.split("\0"):
            if not line:
                continue
            match = re.fullmatch(
                r"100644 blob ([0-9a-f]{40})\t((?:events/[0-9]{10,}|"
                r"(?:requests|reservations|compositions)/[0-9a-f]{64}|queue)\.json)",
                line,
            )
            if not match or match[2] in result:
                raise ControllerError(
                    "E_JOURNAL", "Journal tree has an unexpected path or file mode."
                )
            result[match[2]] = match[1]
        return result

    def history(self) -> tuple[str, list[Transaction]]:
        """Read append-only history within a fresh verification budget."""
        self._guard = verification_guard(self)
        try:
            return self._history()
        finally:
            self._guard = None

    def _history(self) -> tuple[str, list[Transaction]]:
        """Verify anchor, linear ancestry, event and derived file trees read-only.

        Returns: Anchor and chronological transactions, e.g. store.history().
        Raises: ControllerError for missing/replaced history or unexpected contents.
        """
        from cg_release.models import load_record

        head = self._git(
            ["rev-parse", "--verify", f"refs/heads/{self.branch}"]
        ).stdout.strip()
        rows, current, seen = [], head, set()
        while current != self.anchor:
            if current in seen or not re.fullmatch(r"[0-9a-f]{40}", current):
                raise ControllerError(
                    "E_JOURNAL", "Journal ancestry exceeds its bound."
                )
            seen.add(current)
            info = self._git(
                ["show", "-s", "--format=%P%n%an <%ae>", current]
            ).stdout.splitlines()
            if (
                len(info) != 2
                or not re.fullmatch(r"[0-9a-f]{40}", info[0])
                or info[1] != self.writer
            ):
                raise ControllerError(
                    "E_JOURNAL", "Journal ancestry/writer does not match bootstrap."
                )
            rows.append((current, info[0], info[1]))
            current = info[0]
        if self._tree(self.anchor):
            raise ControllerError("E_JOURNAL", "Offline bootstrap tree must be empty.")
        expected, history = {}, []
        for revision, (commit, parent, writer) in enumerate(reversed(rows), 1):
            tree = self._tree(commit)
            event_path = f"events/{revision:010d}.json"
            if event_path not in tree:
                raise ControllerError("E_JOURNAL", "Journal event is missing.")
            event = self._git(["cat-file", "blob", tree[event_path]]).stdout.encode(
                "utf-8"
            )
            try:
                value = decode_json(event.decode())
                from cg_release.recovery_models import event_model

                model = event_model(value["record"])
                record = load_record(model, canonical_bytes(value["record"]))
                for path, content in transaction_files(event, record).items():
                    if content is None:
                        expected.pop(path, None)
                    else:
                        expected[path] = blob_id(content)
            except (KeyError, TypeError, ValueError):
                raise ControllerError(
                    "E_JOURNAL", "Journal transaction data is malformed."
                ) from None
            if tree != expected:
                raise ControllerError(
                    "E_JOURNAL",
                    "Atomic request/reservation tree differs from event history.",
                )
            history.append(Transaction(commit, parent, writer, event))
        return self.anchor, history

    def append(self, parent: str, event: bytes, record: Record) -> None:
        """Append with expected-old ref comparison, e.g. store.append(...).

        Unreachable losing objects may remain; no history or winning ref is removed.
        """
        if not re.fullmatch(r"[0-9a-f]{40}", parent):
            raise ControllerError("E_JOURNAL", "Invalid expected parent.")
        paths = self._tree(parent)
        for path, content in transaction_files(event, record).items():
            if content is None:
                paths.pop(path, None)
            else:
                paths[path] = self._git(
                    ["hash-object", "-w", "--stdin"], text=content.decode("utf-8")
                ).stdout.strip()
        children, root = {}, []
        for path, oid in sorted(paths.items()):
            if "/" not in path:
                root.append(f"100644 blob {oid}\t{path}\n")
                continue
            directory, name = path.split("/")
            children.setdefault(directory, []).append(f"100644 blob {oid}\t{name}\n")
        for directory, entries in sorted(children.items()):
            oid = self._git(["mktree"], text="".join(entries)).stdout.strip()
            root.append(f"040000 tree {oid}\t{directory}\n")
        tree = self._git(["mktree"], text="".join(root)).stdout.strip()
        commit = self._git(
            [
                "-c",
                f"user.name={self.name}",
                "-c",
                f"user.email={self.email}",
                "commit-tree",
                tree,
                "-p",
                parent,
                "-m",
                "Append release controller transaction",
            ]
        ).stdout.strip()
        result = self._git(
            ["update-ref", f"refs/heads/{self.branch}", commit, parent],
            allow_failure=True,
        )
        if result.returncode:
            raise ControllerError(
                "E_CAS", "Competing journal head; re-read before retry."
            )
