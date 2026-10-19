"""Tests must not touch tmux sockets in an inherited TMUX_TMPDIR (#6086)."""

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
LIFESPAN_TEST = (
    "tests/agent_server/test_launch_parity.py"
    "::test_default_and_a_copy_of_it_launch_the_same_agent"
)

pytestmark = pytest.mark.skipif(
    os.name != "posix" or shutil.which("tmux") is None, reason="requires tmux"
)


@pytest.fixture
def inherited_env() -> Iterator[dict[str, str]]:
    """An environment whose TMUX_TMPDIR holds a live legacy-socket session."""
    # /tmp keeps the socket path under the Unix limit on macOS.
    tmux_tmpdir = tempfile.mkdtemp(prefix="oh-inherited-tmux-", dir="/tmp")
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
    env["TMUX_TMPDIR"] = tmux_tmpdir
    subprocess.run(
        ["tmux", "-L", "openhands", "new-session", "-d", "-s", "decoy", "sleep 600"],
        env=env,
        check=True,
    )
    yield env
    subprocess.run(
        ["tmux", "-L", "openhands", "kill-server"], env=env, capture_output=True
    )
    shutil.rmtree(tmux_tmpdir, ignore_errors=True)


def test_lifespan_test_leaves_inherited_tmux_sessions_alone(inherited_env):
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", LIFESPAN_TEST],
        cwd=REPO_ROOT,
        env=inherited_env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert run.returncode == 0, run.stdout[-3000:] + run.stderr[-3000:]

    decoy = subprocess.run(
        ["tmux", "-L", "openhands", "has-session", "-t", "decoy"],
        env=inherited_env,
        capture_output=True,
    )
    assert decoy.returncode == 0, "the test run killed a session it does not own"
