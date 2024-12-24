"""A logger to be used by flows.

Name: Aidan McNay
Date: September 15th, 2024
"""

import logging
import sys
from typing import Self

# Disable root logging except for critical messages
logging.getLogger().setLevel(level=logging.CRITICAL)

# ---------------------------------------------------------------------
# Custom Log Levels: Flow and Step
# ---------------------------------------------------------------------
# Here, we define custom log levels for flow and step messages

SUCCESS = 25  # between WARNING and INFO
FLOW = 26
STEP = 27
logging.addLevelName(SUCCESS, "SUCCESS")
logging.addLevelName(FLOW, "FLOW")
logging.addLevelName(STEP, "STEP")

# ---------------------------------------------------------------------
# Define Formatters
# ---------------------------------------------------------------------


class FlowFormatter(logging.Formatter):
    """A custom formatter to include color in the output."""

    BLUE = "\033[1;34m"
    GREEN = "\033[1;32m"
    PURPLE = "\033[1;35m"
    RESET = "\033[0m"

    flow_fmt = f"{BLUE}[FLOW]{RESET}: %(msg)s"
    flow_fmt_nocolor = "[FLOW]: %(msg)s"
    success_fmt = f"{GREEN}[SUCCESS]{RESET}: %(msg)s"
    success_fmt_nocolor = "[SUCCESS]: %(msg)s"
    step_fmt = f"{PURPLE}[STEP]{RESET}: - %(msg)s"
    step_fmt_nocolor = "[STEP]: - %(msg)s"

    def __init__(
        self: Self,
        fmt: str = "%(levelno)s: %(msg)s",
        datefmt: str = "%m/%d/%Y %H:%M:%S",
        color: bool = True,
    ) -> None:
        """Initialize the formatter.

        Args:
            fmt (str, optional): The format to use. Defaults to
              "%(levelno)s: %(msg)s".
            datefmt (str, optional): The date format to use. Defaults to
              "%m/%d/%Y %H:%M:%S".
            color (bool, optional): Whether to include color. Defaults to
              True.
        """
        logging.Formatter.__init__(self, fmt, datefmt)
        if color:
            self.success = FlowFormatter.success_fmt
            self.flow = FlowFormatter.flow_fmt
            self.step = FlowFormatter.step_fmt
        else:
            self.success = FlowFormatter.success_fmt_nocolor
            self.flow = FlowFormatter.flow_fmt_nocolor
            self.step = FlowFormatter.step_fmt_nocolor

    def format(self: Self, record: logging.LogRecord) -> str:
        """Format a message according to our configurations."""
        new_fmt = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == SUCCESS:
            new_fmt = self.success

        elif record.levelno == FLOW:
            new_fmt = self.flow

        elif record.levelno == STEP:
            new_fmt = self.step

        # Call the original formatter class to do the grunt work
        result = logging.Formatter(new_fmt).format(record)

        return result


file_formatter = FlowFormatter(
    fmt="%(asctime)s %(message)s", datefmt="%m/%d/%Y %H:%M:%S", color=False
)
print_formatter = FlowFormatter(fmt="%(message)s", color=True)

# ---------------------------------------------------------------------
# Verbosity Filter
# ---------------------------------------------------------------------
# Filter out messages when not verbose


class VerboseFilter(logging.Filter):
    """
    A filter to determine when we want to print messages.

    Attributes:
     - verbose (bool): Whether we're verbose or not
    """

    def __init__(self: Self) -> None:
        """Initialize the filter to be verbose."""
        logging.Filter.__init__(self)
        self.verbose = True  # Set default verbosity, to be overwritten

    def set_verbosity(self: Self, verbose: bool) -> None:
        """Set whether we're verbose.

        Args:
            verbose (bool): Whether to be verbose or not
        """
        self.verbose = verbose

    def filter(self: Self, record: logging.LogRecord) -> bool:
        """Determine whether to output a message, given the verbosity.

        Args:
            record (logging.LogRecord): The record to potentially output

        Returns:
            bool: Whether to output or not
        """
        if record.levelno >= logging.CRITICAL:
            return True  # Should output

        return self.verbose  # Output when we're verbose


verbose_filter = VerboseFilter()


def set_verbosity(verbose: bool) -> None:
    """Set the verbosity for the verbosity filter.

    Args:
        verbose (bool): Whether to be verbose or not
    """
    verbose_filter.set_verbosity(verbose)


# ---------------------------------------------------------------------
# Define Handlers
# ---------------------------------------------------------------------
# These determine how we handle logging events
#
# Additionally, we want the capability to dynamically create handlers
# for different file logging

verbose_print = logging.StreamHandler(stream=sys.stdout)
verbose_print.setFormatter(print_formatter)
verbose_print.addFilter(verbose_filter)


def get_file_handler(file_path: str) -> logging.FileHandler:
    """Get a handler to log to the specified file.

    Args:
        file_path (str): The file to log to

    Returns:
        logging.FileHandler: A handler to log to that file
    """
    handler = logging.FileHandler(file_path, mode="w")
    handler.setFormatter(file_formatter)
    return handler


# ------------------------------------------------------------------------
# Make loggers
# ------------------------------------------------------------------------


def get_logger(flow_name: str) -> logging.Logger:
    """Generate a logger to log for the specific flow.

    Args:
        flow_name (str): The name of the flow to log for

    Returns:
        logging.Logger: The logger to log with
    """
    logger = logging.getLogger(f"{flow_name} Logger")
    logger.addHandler(verbose_print)
    logger.setLevel(logging.DEBUG)
    return logger


def add_logfile(logger: logging.Logger, file_path: str) -> None:
    """Add a file for the logger to log at.

    Args:
        logger (logging.Logger): The logger to add the file to
        file_path (str): The file to log at
    """
    logger.addHandler(get_file_handler(file_path))
