"""Bundle the canonical optional profile and static composer in wheel and sdist."""

import os
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Select canonical repo or sdist profile files, never target data."""

    def initialize(self, version, build_data):
        """Add resources to Hatch's build_data for a wheel or sdist (version is unused).

        Returns None; mutates only force_include. Raises ValueError for incomplete
        bundles or an unverified layout. Example: Hatch calls initialize('standard',
        build_data). Unpacked sdists never read surrounding repository resources.
        """
        root = Path(self.root).resolve()
        names = (
            "release_profile_gpid.py",
            "docs-snapshots.js",
            "snapshot-data.js",
            "release-version.js",
        )
        source = root / "profile"
        if source.exists() or (root / "PKG-INFO").exists():
            if not all((source / name).is_file() for name in names):
                raise ValueError("Incomplete bundled profile resources")
        else:
            repository = root.parents[1]
            if (
                root != repository / "packages/cg-release"
                or not (repository / ".github/shared/module-registry.json").is_file()
                or not (repository / "compound-gpid.md").is_file()
                or not (repository / ".git").exists()
            ):
                raise ValueError("Unverified canonical controller package layout")
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=repository,
                    env={
                        k: v for k, v in os.environ.items() if not k.startswith("GIT_")
                    },
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                if (
                    result.returncode
                    or Path(result.stdout.strip()).resolve() != repository
                ):
                    raise ValueError
            except (OSError, ValueError, subprocess.SubprocessError):
                raise ValueError(
                    "Unverified canonical controller Git checkout"
                ) from None
            source = repository / "scripts"
        if source.is_symlink() or any(
            not (source / name).is_file()
            or (source / name).is_symlink()
            or (source / name).resolve().parent != source.resolve()
            for name in names
        ):
            raise ValueError("Incomplete bundled profile or unsafe canonical resources")
        for name in names:
            destination = "profile/" + name
            if self.target_name == "wheel":
                destination = (
                    "_cg_release_gpid.py"
                    if name.endswith(".py")
                    else "cg_release_profile_data/" + name
                )
            build_data["force_include"][str(source / name)] = destination
