import os
import subprocess
import time


def test_main_runs():
    env = os.environ.copy()
    env["PORT"] = "0"
    process = subprocess.Popen(["python", "-m", "src.backend.main"], env=env)
    time.sleep(2)
    poll = process.poll()

    # If poll is not None, the process exited immediately (which is the bug we're testing)
    if poll is not None:
        raise AssertionError(f"Process exited immediately with code {poll}!")

    # Clean up the process if it's still running
    process.terminate()
    process.wait()
