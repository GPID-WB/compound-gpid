"""Dedicated bounded GitHub tree, deployment and composition-discovery reads."""

import math
import re
from datetime import UTC, datetime
from urllib.parse import quote

from cg_release.events import ControllerError


class ProfileReads:
    """Provider operations with fixed query semantics; no user query passthrough."""

    def tree(self, sha: str, *, recursive: bool = False) -> dict:
        """Read an exact tree, e.g. api.tree(sha, recursive=True).

        Args: sha is an exact Git object; recursive is a boolean.
        Returns: A complete, identity-checked tree response; no remote writes.
        Raises: ControllerError for invalid input, truncation or malformed rows.
        """
        if (
            not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
            or type(recursive) is not bool
        ):
            raise ControllerError("E_ENDPOINT", "Invalid exact tree identity.")
        value = self._request(
            f"repos/{self.slug}/git/trees/{sha}"
            + ("?recursive=1" if recursive else ""),
            None,
        )
        if (
            not isinstance(value, dict)
            or value.get("sha") != sha
            or value.get("truncated") is not False
            or not isinstance(value.get("tree"), list)
            or any(
                not isinstance(row, dict) or not isinstance(row.get("path"), str)
                for row in value["tree"]
            )
        ):
            raise ControllerError(
                "E_TREE", "Complete exact tree inventory is required."
            )
        return value

    def deployments(self, environment: str) -> list[dict]:
        """Read one environment, e.g. api.deployments('github-pages').

        Returns: Complete unique deployment objects. Raises ControllerError on
        unsafe environment names, incomplete pages or response shape; read-only.
        """
        if not isinstance(environment, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,100}", environment
        ):
            raise ControllerError("E_ENDPOINT", "Invalid deployment environment.")
        return self._object_pages(
            lambda page: self._request(
                f"repos/{self.slug}/deployments?environment={environment}", page
            )
        )

    def composition_runs(self, workflow: str, *, since: float) -> list[dict]:
        """Read bounded inventory, e.g. api.composition_runs(workflow, since=epoch).

        Returns: Complete run objects for the exact workflow, with an explicit
        1,000-run bound from the sealed creation time, with five minutes of clock
        margin. Older history is not discarded from the journal. Raises
        ControllerError rather than asserting absence from an incomplete inventory.
        Only remote reads occur.
        """
        if not isinstance(workflow, str) or not re.fullmatch(
            r"\.github/workflows/[A-Za-z0-9_-]+\.yml", workflow
        ):
            raise ControllerError("E_ENDPOINT", "Invalid composition workflow.")
        if (
            isinstance(since, bool)
            or not isinstance(since, (int, float))
            or not math.isfinite(since)
            or not 0 <= since <= 253402300799
        ):
            raise ControllerError("E_ENDPOINT", "Invalid composition discovery time.")
        start = datetime.fromtimestamp(max(0, since - 300), UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        created = quote(">=" + start, safe="")
        result, seen = [], set()
        for page in range(1, 11):
            value = self._request(
                f"repos/{self.slug}/actions/workflows/{quote(workflow, safe='')}/runs"
                f"?event=workflow_dispatch&created={created}",
                page,
            )
            if (
                not isinstance(value, dict)
                or type(value.get("total_count")) is not int
                or not 0 <= value["total_count"] <= 1000
                or not isinstance(value.get("workflow_runs"), list)
            ):
                raise ControllerError(
                    "E_PAGINATION",
                    "Composition discovery exceeds its complete inventory bound.",
                )
            rows = value["workflow_runs"]
            for row in rows:
                if (
                    not isinstance(row, dict)
                    or type(row.get("id")) is not int
                    or row["id"] <= 0
                    or row["id"] in seen
                ):
                    raise ControllerError(
                        "E_PAGINATION",
                        "Composition run identity is missing or duplicated.",
                    )
                seen.add(row["id"])
                result.append(row)
            if len(result) == value["total_count"]:
                return result
            if len(rows) != 100:
                break
        raise ControllerError("E_PAGINATION", "Composition inventory is incomplete.")
