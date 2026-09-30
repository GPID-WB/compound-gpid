"""Pure exact-input verification of a registered release-mode matrix run."""

import hashlib

from cg_release.build_models import BuildRegistration, BuildTicket
from cg_release.events import ControllerError
from cg_release.models import canonical_bytes, load_record

MATRIX_JOBS = tuple(
    f"package-{os}-py{version}"
    for os in ("ubuntu-24.04", "windows-latest", "macos-latest")
    for version in ("3.11", "3.12")
) + ("ruff", "release-controller-ci")

REUSE_FIELDS = (
    "repository_id",
    "request_digest",
    "workflow_path",
    "controller_sha",
    "controller_ref",
    "release_sha",
    "release_tree",
    "policy_digest",
    "controller_digest",
    "required_checks_digest",
    "build_inputs_digest",
    "lock_digests",
    "toolchain",
    "profile_version",
    "app_id",
    "required_jobs",
    "build_spec",
    "produces_artifacts",
)


def reuse_key(sealed: dict) -> str:
    """Hash every declared immutable build input, e.g. reuse_key(sealed_request).

    Dispatch nonce and run identity do not change source inputs. Their separate
    registration binding remains mandatory; matching this hash alone proves nothing.
    """
    try:
        load_record(BuildTicket, canonical_bytes(sealed))
        if set(sealed) != set(REUSE_FIELDS) | {"dispatch_nonce"}:
            raise ValueError
        return hashlib.sha256(
            canonical_bytes({k: sealed[k] for k in REUSE_FIELDS})
        ).hexdigest()
    except (KeyError, TypeError, ValueError, RecursionError):
        raise ControllerError(
            "E_BUILD_INPUT", "Complete exact-input build record is required."
        ) from None


def registered_run(sealed: dict, registration: dict, run: dict, suite: dict) -> str:
    """Verify run identity, not success, e.g. before an explicit failed-run retry."""
    key = reuse_key(sealed)
    try:
        load_record(BuildRegistration, canonical_bytes(registration))
        if not all(
            type(value) is int and value > 0
            for value in (
                run["id"],
                run["run_attempt"],
                run["repository"]["id"],
                run["check_suite_id"],
                suite["id"],
                suite["app"]["id"],
            )
        ):
            raise ValueError
        if (
            registration["build_digest"] != key
            or registration["dispatch_nonce"] != sealed["dispatch_nonce"]
            or registration["release_sha"] != sealed["release_sha"]
            or run["id"] != registration["run_id"]
            or run["run_attempt"] != registration["run_attempt"]
            or run["event"] != "workflow_dispatch"
            or run["head_sha"] != sealed["controller_sha"]
            or run["head_branch"] != sealed["controller_ref"]
            or run["path"] != sealed["workflow_path"]
            or run["repository"]["id"] != sealed["repository_id"]
            or suite["id"] != run["check_suite_id"]
            or suite["head_sha"] != sealed["controller_sha"]
            or suite["app"]["id"] != sealed["app_id"]
        ):
            raise ValueError
        return key
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_BUILD_EVIDENCE", "Registered run identity differs."
        ) from None


def verify_build(
    sealed: dict, registration: dict, run: dict, jobs: list[dict], suite: dict
) -> dict:
    """Verify independent GitHub run/jobs/suite metadata against sealed registration.

    Args: sealed and registration come only from the verified controller journal;
        run/jobs/suite come from their exact trusted API endpoints, not job outputs.
    Returns: Reusable matrix provenance, e.g. verify_build(sealed, registration, ...).
    Raises: ControllerError for any failed, skipped, substituted, or missing evidence.
    """
    key = registered_run(sealed, registration, run, suite)
    try:
        if run["status"] != "completed" or run["conclusion"] != "success":
            raise ValueError
        if sealed[
            "workflow_path"
        ] == ".github/workflows/release-controller-ci.yml" and not set(
            MATRIX_JOBS
        ).issubset(sealed["required_jobs"]):
            raise ValueError
        selected, seen, runners = {}, set(), {}
        for job in jobs:
            if (
                type(job["id"]) is not int
                or type(job["run_id"]) is not int
                or type(job["run_attempt"]) is not int
                or job["id"] <= 0
                or job["id"] in seen
                or job["run_id"] != run["id"]
                or job["run_attempt"] != run["run_attempt"]
            ):
                raise ValueError
            seen.add(job["id"])
            if job["name"] in sealed["required_jobs"]:
                if (
                    job["name"] in selected
                    or job["status"] != "completed"
                    or job["conclusion"] != "success"
                ):
                    raise ValueError
                expected_runner = (
                    job["name"].removeprefix("package-").rsplit("-py", 1)[0]
                    if job["name"] in MATRIX_JOBS and job["name"].startswith("package-")
                    else "ubuntu-24.04"
                )
                if (
                    type(job["runner_id"]) is not int
                    or job["runner_id"] <= 0
                    or not isinstance(job["runner_name"], str)
                    or not job["runner_name"]
                    or job["labels"] != [expected_runner]
                ):
                    raise ValueError
                selected[job["name"]] = job["id"]
                runners[job["name"]] = {
                    "id": job["runner_id"],
                    "name": job["runner_name"],
                    "labels": job["labels"],
                }
        if set(selected) != set(sealed["required_jobs"]) or len(
            set(sealed["required_jobs"])
        ) != len(sealed["required_jobs"]):
            raise ValueError
        return {
            "reuse_key": key,
            "release_sha": sealed["release_sha"],
            "release_tree": sealed["release_tree"],
            "controller_sha": sealed["controller_sha"],
            "workflow_path": sealed["workflow_path"],
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "jobs": selected,
            "runners": runners,
            "dispatch_nonce": registration["dispatch_nonce"],
        }
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_BUILD_EVIDENCE",
            "Registered release-mode run or required job identities differ.",
        ) from None
