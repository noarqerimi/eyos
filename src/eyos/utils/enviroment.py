import functools
import os
from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo


@functools.cache
def get_latest_tag() -> str:
    import subprocess

    command = ["git", "describe", "--tags", "--abbrev=0"]
    completed_process = subprocess.run(command, stdout=subprocess.PIPE)
    if completed_process.returncode != 0:
        return "unknown"
    return completed_process.stdout.decode().strip()


@functools.cache
def environment_details() -> Dict[str, str]:
    """
    This to see the build date and git hash of the container.
    Intended use is as a public endpoint (such as `/`) in API projects.
    Shows `unknown` when run locally.
    """

    if "IMAGE_BUILD_DATE" in os.environ:
        unix_timestamp = int(os.environ["IMAGE_BUILD_DATE"])
        image_build_date = datetime.fromtimestamp(unix_timestamp, tz=ZoneInfo("Europe/Copenhagen")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        image_build_date = "unknown"

    return {
        "status": "OK",
        "git_hash": os.getenv("GIT_COMMIT_HASH", "unknown"),
        "image_build_date": image_build_date,
        "version": get_latest_tag(),
    }
