"""Publication-App-only Git/GitHub operations with no force, clobber or delete API."""

import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

from cg_release.events import ControllerError
from cg_release.models import canonical_bytes
from cg_release.policy import safe_ref


class ReadOnlyPublication:
    """Observe an already-published release; never repair it through a new write."""

    def __init__(self, remote):
        self.remote = remote

    def __getattr__(self, name):
        return getattr(self.remote, name)

    def _deny(self, *args, **kwargs):
        raise ControllerError(
            "E_PUBLICATION_READONLY",
            "Published recovery cannot create, replace or republish remote objects.",
        )

    push_tag = create_draft = upload = publish = _deny


class GitHubPublicationRemote:
    """Use an independently authenticated reader, e.g. GitHubPublicationRemote(api).

    The caller must supply a publication-role runner; this class cannot update the
    journal. API response upload URLs and target-source scripts are never executed.
    """

    def __init__(self, api, *, refs=None, releases=None):
        self.api = api
        self._refs, self._releases = refs, releases

    def _write(self, method, endpoint, payload=None, *, file=None, media_type=None):
        api = self.api
        if method not in {"POST", "PATCH"}:
            raise ControllerError("E_PUBLICATION", "Unsupported publication operation.")
        argv = [
            "api",
            "--method",
            method,
            "--hostname",
            api.host,
            "--include",
            "--input",
            str(file) if file else "-",
        ]
        if media_type:
            argv += ["--header", "Content-Type: " + media_type]
        argv.append(endpoint)
        result = api.runner(
            "gh",
            argv,
            cwd=api.cwd,
            timeout=min(api.read_seconds, api.remaining()),
            allow_failure=True,
            **(
                {"input_text": canonical_bytes(payload).decode()}
                if file is None
                else {}
            ),
        )
        match = re.match(r"HTTP/[0-9.]+ ([0-9]{3})(?: |\r?\n)", result.stdout)
        status = int(match[1]) if match else None
        if result.returncode or status not in {200, 201, 204}:
            code = {401: "E_AUTH", 403: "E_FORBIDDEN", 404: "E_NOT_FOUND"}.get(
                status, "E_WRITE_UNKNOWN"
            )
            raise ControllerError(
                code,
                "Publication write failed; reconcile exact remote objects. "
                "Check workflow-file App permissions for HTTP 403/404.",
            )

    def observe_tag(self, tag):
        """Read complete refs then the exact annotated object, e.g. observe_tag(tag)."""
        safe_ref(tag)
        matches = [
            r
            for r in (self.api.refs() if self._refs is None else self._refs)
            if r["ref"] == "refs/tags/" + tag
        ]
        if not matches:
            return None
        if len(matches) != 1 or matches[0]["object"]["type"] != "tag":
            raise ControllerError(
                "E_TAG_CONFLICT", "Managed tag is ambiguous or lightweight."
            )
        value = self.api.get("git/ref/tags/" + quote(tag, safe=""))
        oid = value["object"]["sha"]
        obj = self.api.get("git/tags/" + oid)
        if (
            value["ref"] != "refs/tags/" + tag
            or any(
                value["object"].get(k) != matches[0]["object"].get(k)
                for k in ("sha", "type")
            )
            or obj["sha"] != oid
            or obj["tag"] != tag
            or obj["object"]["type"] != "commit"
        ):
            raise ControllerError(
                "E_TAG_CONFLICT", "Remote tag-object identity differs."
            )
        return {"oid": oid, "commit": obj["object"]["sha"], "type": "tag"}

    def push_tag(self, tag, value, sha):
        """Fetch commit data and push one exact ref, e.g. push_tag(tag, object, sha)."""
        safe_ref(tag)
        if not re.fullmatch(r"[0-9a-f]{40}", sha) or not re.fullmatch(
            r"[0-9a-f]{40}", value["oid"]
        ):
            raise ControllerError(
                "E_TAG_CONFLICT", "Invalid exact tag or source object."
            )
        api = self.api
        with TemporaryDirectory(prefix="cg-release-tag-") as directory:
            root = Path(directory)
            env = {
                k: v
                for k, v in os.environ.items()
                if k.upper()
                in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC"}
            }
            env.update(
                GIT_CONFIG_NOSYSTEM="1",
                GIT_CONFIG_GLOBAL=os.devnull,
                GIT_TERMINAL_PROMPT="0",
            )
            config = [
                "-c",
                "credential.helper=",
                "-c",
                "credential.helper=!gh auth git-credential",
                "-c",
                "protocol.allow=never",
                "-c",
                "protocol.https.allow=always",
                "-c",
                "http.followRedirects=false",
            ]

            def git(args, **kwargs):
                return api.runner(
                    "git",
                    [*config, *args],
                    cwd=root,
                    environment=env,
                    timeout=min(20, api.remaining()),
                    **kwargs,
                )

            git(["init", "--bare", "."])
            url = f"https://{api.host}/{api.slug}.git"
            git(["fetch", "--no-tags", "--no-recurse-submodules", "--", url, sha])
            result = git(
                ["hash-object", "-t", "tag", "--stdin", "-w"], input_text=value["text"]
            )
            if result.stdout.strip() != value["oid"]:
                raise ControllerError(
                    "E_TAG_CONFLICT", "Persisted tag bytes have another object ID."
                )
            git(["push", "--porcelain", "--", url, value["oid"] + ":refs/tags/" + tag])

    def observe_release(self, tag):
        """Resolve draft or published Release by exact tag from complete inventory."""
        matches = [
            r
            for r in (
                self.api.pages("releases") if self._releases is None else self._releases
            )
            if r.get("tag_name") == tag
        ]
        if len(matches) > 1:
            raise ControllerError("E_RELEASE_CONFLICT", "Duplicate Release identity.")
        return matches[0] if matches else None

    def create_draft(self, tag, sha, notes, prerelease):
        """Stage a non-latest draft, e.g. create_draft(tag, sha, notes, True)."""
        self._write(
            "POST",
            f"repos/{self.api.slug}/releases",
            {
                "tag_name": tag,
                "target_commitish": sha,
                "name": tag,
                "body": notes,
                "draft": True,
                "prerelease": prerelease,
                "make_latest": "false",
            },
        )

    def inventory(self, release_id):
        """Return complete Release asset metadata, e.g. inventory(123)."""
        return self.api.pages(f"releases/{release_id}/assets")

    def download(self, asset):
        """Download bounded bytes by asset ID, e.g. download(metadata)."""
        if (
            type(asset.get("id")) is not int
            or asset["id"] <= 0
            or type(asset.get("size")) is not int
            or not 0 <= asset["size"] <= 64 * 1024 * 1024
        ):
            raise ControllerError("E_ASSET", "Invalid remote asset identity.")
        api = self.api
        result = api.runner(
            "gh",
            [
                "api",
                "--method",
                "GET",
                "--hostname",
                api.host,
                "--header",
                "Accept: application/octet-stream",
                f"repos/{api.slug}/releases/assets/{asset['id']}",
            ],
            cwd=api.cwd,
            timeout=min(api.read_seconds, api.remaining()),
            binary_output=True,
            max_output_bytes=min(64 * 1024 * 1024, asset["size"] + 1),
        )
        return result.stdout

    def upload(self, release_id, item, raw):
        """Upload one new asset at the derived API host, e.g. upload(id, item, raw)."""
        if not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}", item["name"]
        ) or not re.fullmatch(r"[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+", item["media_type"]):
            raise ControllerError("E_ASSET", "Unsafe asset name or media type.")
        api = self.api
        host = "uploads.github.com" if api.host == "github.com" else api.host
        prefix = "" if api.host == "github.com" else "/api/uploads"
        endpoint = (
            f"https://{host}{prefix}/repos/{api.slug}/releases/{release_id}/assets"
            f"?name={quote(item['name'], safe='')}"
        )
        with TemporaryDirectory(prefix="cg-release-asset-") as directory:
            path = Path(directory) / "asset"
            path.write_bytes(raw)
            self._write("POST", endpoint, file=path, media_type=item["media_type"])

    def publish(self, release_id, latest):
        """Publish with explicit latest policy, e.g. publish(123, False)."""
        self._write(
            "PATCH",
            f"repos/{self.api.slug}/releases/{release_id}",
            {"draft": False, "make_latest": "true" if latest else "false"},
        )

    def latest_id(self):
        """Read and verify current latest endpoint; absence is not an auth fallback."""
        try:
            value = self.api.get("releases/latest")
        except ControllerError as error:
            if error.code != "E_NOT_FOUND":
                raise
            if any(
                r.get("draft") is False and r.get("prerelease") is False
                for r in self.api.pages("releases")
            ):
                raise ControllerError(
                    "E_LATEST",
                    "Latest endpoint is absent despite published stable releases.",
                ) from None
            return None
        if (
            type(value.get("id")) is not int
            or value["id"] <= 0
            or value.get("draft") is not False
            or value.get("prerelease") is not False
        ):
            raise ControllerError("E_LATEST", "Latest Release identity is invalid.")
        return value["id"]
