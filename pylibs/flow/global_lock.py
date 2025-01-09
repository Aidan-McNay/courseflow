"""A lock across Python processes, implemented using fcntl.lockf.

Author: Aidan McNay
Date: January 9th, 2025
"""

import fcntl
import os
import tempfile
from types import TracebackType
from typing import Literal, Optional, Type

TMP_DIR_NAME = os.path.join(tempfile.gettempdir(), "courseflow")

# -----------------------------------------------------------------------------
# GLock
# -----------------------------------------------------------------------------
# A global lock for a particular identifier


class GLock:
    """A global lock across Python processes.

    GLock is implemented using fcntl.lockf, which locks a file with the same
    name as the string descriptor. This allows different Python processes to
    be properly synchronized when accessing shared resources, such as
    storage mediums for RecordStorers.
    """

    def __init__(self: "GLock", id: str, mode: Literal["r", "w"] = "w") -> None:
        """Initialize the lock with a given filename.

        This will be created in the /tmp/courseflow directory, which will
        be created if it doesn't already exist.
        """
        if not os.path.isdir(TMP_DIR_NAME):
            os.mkdir(TMP_DIR_NAME)

        self.file_path = os.path.join(TMP_DIR_NAME, id)
        self.mode = mode
        if mode == "w":
            self.lock_cmd = fcntl.LOCK_EX
        else:
            self.lock_cmd = fcntl.LOCK_SH

        # Create the file if it doesn't exist
        with open(self.file_path, "w") as _:
            pass

    def __enter__(self: "GLock") -> "GLock":
        """Acquire the lock using fcntl.lockf."""
        self.fd = open(self.file_path, self.mode)
        fcntl.lockf(self.fd, self.lock_cmd)
        return self

    def __exit__(
        self: "GLock",
        exctype: Optional[Type[BaseException]],
        excinst: Optional[BaseException],
        exctb: Optional[TracebackType],
    ) -> None:
        """Release the lock by closing the file handle."""
        self.fd.close()
