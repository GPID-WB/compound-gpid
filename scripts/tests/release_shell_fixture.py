"""Real shell fixture executables; only interpreter/process edges are substitutes."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = r"""
import json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[1]).stem
args = sys.argv[2:]
with open(os.environ['SHELL_TRACE'], 'a', encoding='utf-8') as output:
    output.write(json.dumps([name, args]) + '\n')
if args == ['--version']:
    mode = os.environ.get('CANDIDATE_' + name, 'valid')
    sys.stdout.write('Python was not found; Microsoft Store\n' if mode == 'stub' else 'Python 3.12.0\n')
    sys.exit(9009 if mode == 'stub' else 0)
if args and args[0] == '-c':
    sys.exit(1 if os.environ.get('CANDIDATE_' + name) == 'old' else 0)
if args and args[0].endswith('cg_release_cli.py'):
    sys.exit(subprocess.call([os.environ['REAL_PYTHON'], *args]))
pathlib.Path(os.environ['ARGV_RECORD']).write_text(json.dumps(args), encoding='utf-8')
sys.exit(int(os.environ['CHILD_EXIT']))
"""
CSHARP = r"""
using System;
using System.Diagnostics;
using System.Reflection;
using System.Text;
public class Fixture {
  static string Quote(string value) {
    var result = new StringBuilder("\""); int slashes=0;
    foreach (char c in value) {
      if (c=='\\') { slashes++; continue; }
      if (c=='"') result.Append('\\', slashes*2+1);
      else result.Append('\\', slashes);
      result.Append(c); slashes=0;
    }
    result.Append('\\', slashes*2); return result.Append('"').ToString();
  }
  public static int Main(string[] args) {
    var argv = new StringBuilder(Quote(Environment.GetEnvironmentVariable("DISPATCH")));
    argv.Append(" ").Append(Quote(Assembly.GetExecutingAssembly().Location));
    foreach (string arg in args) argv.Append(" ").Append(Quote(arg));
    var info = new ProcessStartInfo(Environment.GetEnvironmentVariable("REAL_PYTHON"), argv.ToString());
    info.UseShellExecute=false;
    var child=Process.Start(info); child.WaitForExit(); return child.ExitCode;
  }
}
"""


def setup_shell(tmp_path, kind, candidates=("python3",), *, shim=False):
    """Copy the real launchers and Python router, then supply fake OS executables."""
    root = tmp_path / "installation with spaces"
    binaries = tmp_path / "candidate executables"
    binaries.mkdir()
    (root / "bin").mkdir(parents=True)
    (root / "scripts").mkdir()
    for name in ["cg-release", "cg-release.cmd"]:
        shutil.copy2(ROOT / "bin" / name, root / "bin" / name)
    (root / "bin/cg-release").chmod(0o755)
    shutil.copy2(ROOT / "scripts/cg_release_cli.py", root / "scripts/cg_release_cli.py")
    dispatch = tmp_path / "dispatch.py"
    dispatch.write_text(DISPATCH, encoding="utf-8")
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("PYTHON")
    }
    env.update(
        REAL_PYTHON=sys.executable,
        DISPATCH=str(dispatch),
        ARGV_RECORD=str(tmp_path / "argv.json"),
        SHELL_TRACE=str(tmp_path / "trace.jsonl"),
        CHILD_EXIT="37",
    )
    if kind == "cmd":
        compiler = (
            Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        )
        assert compiler.is_file(), (
            "Supported Windows host must provide the fixture compiler"
        )
        source = tmp_path / "Fixture.cs"
        source.write_text(CSHARP)
        binary = binaries / "fixture.exe"
        result = subprocess.run(
            [str(compiler), "/nologo", "/out:" + str(binary), str(source)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        for name in [*candidates, "pwsh"]:
            if name in (candidates if shim is True else shim or ()):
                (binaries / (name + ".cmd")).write_text(
                    '@echo off\r\n"%~dp0fixture.exe" %*\r\nexit /b %ERRORLEVEL%\r\n'
                )
            else:
                shutil.copy2(binary, binaries / (name + ".exe"))
        child = root / "packages/cg-release/.venv/Scripts/python.exe"
        child.parent.mkdir(parents=True)
        shutil.copy2(binary, child)
        (binaries / "cg-release.cmd").write_text("@exit /b 99\r\n")
        env["PATH"] = (
            str(binaries) + os.pathsep + str(Path(os.environ["WINDIR"]) / "System32")
        )
        shell = os.environ["COMSPEC"]
    else:
        shell = (
            "C:/Program Files/Git/bin/bash.exe"
            if os.name == "nt"
            else shutil.which("bash")
        )
        assert shell and Path(shell).is_file(), "Bash is required on the selected host"
        # The real launcher uses /usr/bin/env bash, even when invoked by Bash.
        bash_entry = binaries / "bash"
        bash_entry.write_text("#!/bin/bash\nexec " + shlex.quote(Path(shell).as_posix()) + ' "$@"\n', newline="\n")
        bash_entry.chmod(0o755)
        for name in [*candidates, "pwsh"]:
            path = binaries / name
            path.write_text(
                '#!/bin/bash\nexec "$REAL_PYTHON" "$DISPATCH" "$0" "$@"\n', newline="\n"
            )
            path.chmod(0o755)
        (binaries / "dirname").write_text(
            '#!/bin/bash\nprintf "%s\\n" "${1%/*}"\n', newline="\n"
        )
        (binaries / "dirname").chmod(0o755)
        child = root / (
            "packages/cg-release/.venv/Scripts/python.exe"
            if os.name == "nt"
            else "packages/cg-release/.venv/bin/python"
        )
        child.parent.mkdir(parents=True)
        # Python's Windows subprocess requires a PE executable even when Bash chose it.
        if os.name == "nt":
            compiler = (
                Path(os.environ["WINDIR"])
                / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
            )
            source = tmp_path / "Fixture.cs"
            source.write_text(CSHARP)
            # Use the same neutral assembly as CMD before copying to mock names.
            binary = binaries / "fixture.exe"
            subprocess.run(
                [str(compiler), "/nologo", "/out:" + str(binary), str(source)],
                check=True,
                capture_output=True,
                timeout=30,
            )
            shutil.copy2(binary, child)
            shutil.copy2(binary, binaries / "pwsh.exe")
            (binaries / "pwsh").unlink()
        else:
            shutil.copy2(binaries / candidates[-1], child)
            child.chmod(0o755)
        (binaries / "cg-release").write_text("#!/bin/bash\nexit 99\n", newline="\n")
        (binaries / "cg-release").chmod(0o755)
        env["PATH"] = str(binaries)
    return root, env, str(shell)


def invoke(root, env, shell, args, kind):
    """Execute the actual OS shell and return status plus exact recorded child argv."""
    if kind == "cmd":
        command = (
            '"'
            + subprocess.list2cmdline([str(root / "bin/cg-release.cmd"), *args])
            + '"'
        )
        argv = '"' + shell + '" /d /s /c ' + command
        input_text = None
    else:
        argv = [shell, "--noprofile", "--norc"]
        input_text = (
            "exec " + shlex.join([(root / "bin/cg-release").as_posix(), *args]) + "\n"
        )
    result = subprocess.run(
        argv,
        cwd=root.parent,
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    record = Path(env["ARGV_RECORD"])
    return result, json.loads(record.read_text()) if record.exists() else None
