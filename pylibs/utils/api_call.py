"""Utilities for calling API functions.

Author: Aidan McNay
Date: October 3rd, 2024
"""

import sys
from typing import Callable, TypeVar

# -----------------------------------------------------------------------------
# retry_call
# -----------------------------------------------------------------------------

ReturnType = TypeVar("ReturnType")
ArgsType = TypeVar("ArgsType")
KwargsType = TypeVar("KwargsType")

NUM_TRIES = 10


def retry_call(
    func: Callable[..., ReturnType], *args: ArgsType, **kwargs: KwargsType
) -> ReturnType:
    """Try a function a given number of times.

    Args:
        func (Callable[[...], ReturnType]): The function to try
        num_tries (int, optional): The number of times to try calling the
          function. Defaults to 10.

    Returns:
        ReturnType: What the function returned, if it succeeded
    """
    num_tries = NUM_TRIES
    while num_tries > 0:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            num_tries -= 1
            if num_tries == 0:
                raise e
    # Never reach here
    sys.exit(1)
