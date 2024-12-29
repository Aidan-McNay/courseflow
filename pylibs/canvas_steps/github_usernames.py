"""Get the GitHub usernames from the appropriate quiz on Canvas.

Author: Aidan McNay
Date: September 16th, 2024
"""

import canvasapi
from threading import Lock
from typing import Any, Callable, Optional, Self

from canvas_steps import _course
from github_steps import _github
from flow.flow_steps import FlowUpdateStep
from records.student_record import StudentRecord

# ------------------------------------------------------------------------
# valid_username
# ------------------------------------------------------------------------


def valid_username(username: str) -> bool:
    """Return whether a given GitHub username is valid.

    Args:
        username (str): The username is valid

    Returns:
        bool: Whether such a user exists on GitHub
    """
    try:
        _github.get_user(username)
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# GitHubUsernames
# -----------------------------------------------------------------------------


class GitHubUsernames(FlowUpdateStep[StudentRecord]):
    """An update step for getting student's GitHub usernames from Canvas.

    This relies on having a quiz where they previously submitted their
    usernames.
    """

    description = (
        "Get usernames from a 'Fill in the Blank' " "question on a Canvas Quiz"
    )

    question_id_url = (
        "https://community.canvaslms.com/t5/Canvas-Developers-Group/"
        "If-I-have-a-Course-ID-Quiz-ID-and-a-Question-ID-can-I-create-a/"
        "td-p/600774"
    )

    config_types = [
        ("quiz_id", int, "The ID of the Canvas Quiz (from URL)"),
        (
            "question_id",
            int,
            (
                "The ID of the question "
                f"(API or Inspect Element - {question_id_url}"
            ),
        ),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        # Make sure that the quiz exists with the given question
        try:
            github_quiz = _course.get_quiz(self.configs.quiz_id)
        except Exception:
            raise Exception(f"No quiz with ID '{self.configs.quiz_id}'")

        questions = github_quiz.get_questions()
        if self.configs.question_id not in [
            question.id for question in questions
        ]:
            error = f"No question with ID '{self.configs.question_id}'"
            for question in questions:
                error += f"\n - {question.question_name}: {question.id}"
            raise Exception(error)

    def username_from_submission(
        self: Self, quiz_submission: canvasapi.quiz.QuizSubmission
    ) -> str:
        """Determine a student's answer from the submission events.

        Args:
            self (Self): The relevant update step
            quiz_submission (canvasapi.quiz.QuizSubmission): The submission to
              inspect the events of

        Raises:
            AttributeError: Raised if the submission doesn't contain an answer

        Returns:
            str: The username that was submitted
        """
        username: Optional[str] = None
        for event in quiz_submission.get_submission_events():
            if event.event_type == "question_answered":
                for event_data in event.event_data:
                    if event_data["quiz_question_id"] == str(
                        self.configs.question_id
                    ):
                        username = event_data["answer"]

        if username is None:
            raise AttributeError("No username specified in the response")
        return username

    def update_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Update our records with students' GitHub usernames.

        Args:
            records (list[StudentRecord]): The list of records to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            set_metadata (Callable[[str, Any], None]): A function to set
              global metadata within the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        github_quiz = _course.get_quiz(self.configs.quiz_id)
        submissions = github_quiz.get_submissions()
        uid_submission_mapping = {
            quiz_submission.user_id: quiz_submission
            for quiz_submission in submissions
        }
        netid_uid_mapping = {
            user.login_id: user.id for user in _course.get_users()
        }

        for record, lock in records:
            with lock:
                if record.enrolled and (
                    (record.github_username is None)
                    or (record.github_valid is False)
                ):
                    # Try to get the correct value
                    uid = netid_uid_mapping[record.netid]
                    if uid in uid_submission_mapping:
                        # Get their submission
                        try:
                            username = self.username_from_submission(
                                uid_submission_mapping[uid]
                            )
                            record.github_username = username
                            record.github_valid = valid_username(
                                record.github_username
                            )
                            if record.github_valid:
                                logger(
                                    f"Valid username for {record.netid}: "
                                    f"{record.github_username}"
                                )
                            else:
                                logger(
                                    f"Invalid username for {record.netid}: "
                                    f"{record.github_username}"
                                )
                        except Exception as e:
                            logger(
                                f"Error getting username for {record.netid}: "
                                f"{str(e)}"
                            )
                            continue
                    else:
                        logger(
                            f"No GitHub username submission for {record.netid}"
                        )
