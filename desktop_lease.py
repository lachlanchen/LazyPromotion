#!/usr/bin/env python3
"""Coordinate finite checks with manual use of the one project desktop."""

from __future__ import annotations

import argparse
import fcntl
import os
import signal
import socket
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local" / "runtime"
LOCK_PATH = RUNTIME / "desktop-lifecycle.lock"
SCRIPT = ROOT / "scripts" / "desktop.sh"
LEASE_ENV = "LAZYPROMOTION_DESKTOP_LEASE_FD"
PORTS = (5936, 6136, 9436)
COMPONENTS = {
    "xvfb": "Xvfb :116",
    "x11vnc": "-rfbport 5936",
    "novnc": "127.0.0.1:6136",
    "chrome": str(ROOT / ".local" / "browser" / "profile"),
    "fit": "fit_window_loop",
}


class DesktopBusy(RuntimeError):
    pass


@contextmanager
def lifecycle_lease(path: Path = LOCK_PATH):
    for parent in (path.parent.parent, path.parent):
        if parent.is_symlink():
            raise RuntimeError("unsafe desktop lease directory")
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise RuntimeError("unsafe desktop lease file")
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DesktopBusy("another desktop operation owns the lease") from exc
        yield fd
    finally:
        # Closing this descriptor releases this process's lease. Children do not
        # keep it: desktop.sh closes its inherited copy before starting tmux.
        os.close(fd)


def stack_command(action: str, lease_fd: int, *, timeout: int = 90):
    if action not in {"start", "stop", "restart", "status"}:
        raise ValueError("unsupported desktop action")
    env = dict(os.environ)
    env[LEASE_ENV] = str(lease_fd)
    env["LAZYPROMOTION_REFRESH_REGISTERED_VIEWER"] = "0"
    return subprocess.run(
        [str(SCRIPT), action], cwd=ROOT, env=env, pass_fds=(lease_fd,),
        capture_output=True, text=True, timeout=timeout, check=False,
    )


def process_identity(pid: int) -> tuple[int, str] | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return None
        command = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()
        return int(fields[19]), command
    except (FileNotFoundError, ProcessLookupError):
        return None


def stack_snapshot() -> dict:
    snapshot = {}
    for name, marker in COMPONENTS.items():
        path = RUNTIME / f"{name}.pid"
        try:
            pid = int(path.read_text().strip())
        except FileNotFoundError:
            continue
        identity = process_identity(pid)
        if identity is not None and marker in identity[1]:
            snapshot[name] = (pid, identity[0])
    supervisor = subprocess.run(
        ["tmux", "list-panes", "-t", "=lazypromotion-browser", "-F", "#{pane_pid}"],
        capture_output=True, text=True, timeout=5, check=False,
    )
    if supervisor.returncode == 0:
        rows = supervisor.stdout.splitlines()
        if len(rows) != 1 or not rows[0].isdigit():
            raise RuntimeError("ambiguous desktop supervisor")
        pid = int(rows[0])
        identity = process_identity(pid)
        if identity is not None:
            if str(SCRIPT) not in identity[1] or "_serve" not in identity[1]:
                raise RuntimeError("desktop supervisor ownership is unknown")
            snapshot["supervisor"] = (pid, identity[0])
    return snapshot


def ownership_unchanged(expected: dict) -> bool:
    current = stack_snapshot()
    # A component may have exited. Any replacement, including PID reuse, is not
    # ours to terminate. The lease prevents cooperative launchers replacing it.
    if any(expected.get(name) != identity for name, identity in current.items()):
        return False
    for name, (pid, started) in expected.items():
        identity = process_identity(pid)
        if identity is not None and (
            identity[0] != started or current.get(name) != (pid, started)
        ):
            return False
    return True


def ports_closed() -> bool:
    for port in PORTS:
        with socket.socket() as connection:
            connection.settimeout(0.2)
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                return False
    return True


def resources_available() -> bool:
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        memory[key] = int(value.split()[0])
    if memory["MemAvailable"] < 24 * 1024 * 1024:
        return False
    total = memory["SwapTotal"]
    return not total or (total - memory["SwapFree"]) * 4 <= total * 3


def run_check_command(command: list[str], *, timeout: int) -> int:
    process = subprocess.Popen(
        command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        raise


def run_owned_check(command: list[str], *, timeout: int = 180) -> dict:
    if not command or timeout < 1 or timeout > 300:
        raise ValueError("a finite command and timeout of at most 300 seconds are required")
    result = {"state": "not_started", "desktop_started": False, "desktop_stopped": False}
    try:
        with lifecycle_lease() as lease_fd:
            if stack_snapshot() or not ports_closed():
                return {**result, "state": "skipped_active_or_partial_desktop"}
            status = stack_command("status", lease_fd)
            if sum(line.endswith(" stopped") for line in status.stdout.splitlines()) != 5:
                return {**result, "state": "skipped_unknown_desktop_state"}
            if not resources_available():
                return {**result, "state": "skipped_resource_pressure"}
            expected = None
            try:
                started = stack_command("start", lease_fd)
                expected = stack_snapshot()
                result["desktop_started"] = bool(expected)
                if started.returncode != 0 or not all(name in expected for name in COMPONENTS):
                    result["state"] = "desktop_start_failed"
                else:
                    returncode = run_check_command(command, timeout=timeout)
                    result.update(
                        state="checked" if returncode == 0 else "check_failed",
                        check_returncode=returncode,
                    )
            except subprocess.TimeoutExpired:
                result["state"] = "check_timeout"
            except KeyboardInterrupt:
                result["state"] = "check_interrupted"
            except Exception:
                result["state"] = "check_failed"
            finally:
                try:
                    if expected is None:
                        expected = stack_snapshot()
                    if not ownership_unchanged(expected):
                        result["state"] = "cleanup_refused_ownership_changed"
                    else:
                        stopped = stack_command("stop", lease_fd)
                        result["desktop_stopped"] = (
                            stopped.returncode == 0 and not stack_snapshot() and ports_closed()
                        )
                        if not result["desktop_stopped"]:
                            result["state"] = "desktop_cleanup_failed"
                except Exception:
                    result["state"] = "desktop_cleanup_failed"
    except DesktopBusy:
        result["state"] = "skipped_desktop_lease_busy"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "stop", "restart"))
    args = parser.parse_args()
    try:
        with lifecycle_lease() as lease_fd:
            result = stack_command(args.action, lease_fd)
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(result.returncode)
    except DesktopBusy:
        print("A finite review owns the project desktop; no action was taken.", file=sys.stderr)
        raise SystemExit(75)
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("Desktop lifecycle operation failed; inspect the private runtime status.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
