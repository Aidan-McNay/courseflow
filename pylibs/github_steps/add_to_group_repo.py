"""Add students to their personal repositories.

Author: Aidan McNay
Date: September 18th, 2024
"""

import github
from threading import Lock
from typing import Any, Callable, cast, Optional, Self, Type

from github_steps import _github, _org
from flow.flow_steps import FlowPropagateStep, ValidConfigTypes
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# AddToPersonalRepos
# -----------------------------------------------------------------------------


class AddToGroupRepos(FlowPropagateStep[StudentRecord]):
    """A propagate step to give students permission to their personal repos."""

    description = "Give students access to their group repos"

    config_types: list[tuple[str, Type[ValidConfigTypes], str]] = [
        (
            "name_format",
            str,
            (
                "The format to create new teams with. <num> will"
                "be replaced with the team's number"
            ),
        ),
        (
            "num_places",
            int,
            (
                "The number of places to represent the group number in "
                "the team. Ex. 2 places -> 06"
            ),
        ),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        if "<num>" not in self.configs.name_format:
            raise Exception(
                "<num> not present in format; all teams would be identical!"
            )
        return

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Add students to their personal repositories.

        We also look at the metadata 'old_groups' to remove users from
        previous groups.

        Args:
            records (list[RecordType]): The list of records to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            get_metadata (Callable[[str], Any],): A function to retrieve global
              metadata previously set in the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        # Get the teams to make
        teams: list[str] = []
        netid_team_mapping: dict[str, str] = {}
        team_repos_mapping: dict[str, list[str]] = {}
        made_teams: list[github.Team.Team] = list(_org.get_teams())

        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and (record.group_num is not None)
                    and (record.group_repo_name is not None)
                ):
                    group_name = self.configs.name_format.replace(
                        "<num>",
                        str(record.group_num).zfill(self.configs.num_places),
                    )
                    if record.group_repo_name not in teams:
                        teams.append(group_name)
                    netid_team_mapping[record.netid] = group_name

                    if group_name not in team_repos_mapping:
                        team_repos_mapping[group_name] = [
                            record.group_repo_name
                        ]
                    else:
                        team_repos_mapping[group_name] = team_repos_mapping[
                            group_name
                        ] + [record.group_repo_name]

        # Make the teams
        curr_teams = [team.name for team in _org.get_teams()]
        for team_name in teams:
            if team_name not in curr_teams:
                if debug:
                    logger(f"DEBUG: Avoiding creating team {team_name}")
                else:
                    made_team = _org.create_team(
                        name=team_name,
                        repo_names=[
                            _org.get_repo(repo_name)
                            for repo_name in team_repos_mapping[team_name]
                        ],
                        privacy="secret",
                        notification_setting="notifications_enabled",
                        permission="push",
                    )
                    logger(f"Created group team: {team_name}")
                    made_teams.append(made_team)

        # Remove users from old teams
        old_groups = cast(dict[str, int], get_metadata("old_groups"))
        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and (record.github_username is not None)
                    and record.netid in old_groups
                ):
                    old_group_name = self.configs.name_format.replace(
                        "<num>",
                        str(old_groups[record.netid]).zfill(
                            self.configs.num_places
                        ),
                    )
                    group_team = _org.get_team_by_slug(old_group_name)
                    user = _github.get_user(record.github_username)
                    if isinstance(
                        user,
                        github.AuthenticatedUser.AuthenticatedUser,
                    ):
                        logger(f"Avoiding removing {user.login} (yourself?)")
                        continue
                    else:
                        if user.login in [
                            member.login for member in group_team.get_members()
                        ]:
                            group_team.remove_membership(user)
                            record.added_to_group = False
                            logger(
                                f"Removed {record.netid} from "
                                f"old team {old_group_name}"
                            )

        # Add users to their team
        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and record.github_accepted
                    and (not record.added_to_group)
                ):
                    if record.github_username is None:
                        logger(
                            f"{record.netid} accepted to GitHub, "
                            "but no username; ignoring"
                        )
                        continue
                    if debug:
                        logger(
                            f"DEBUG: Not adding {record.netid} to group team"
                        )
                        continue
                    try:
                        user = _github.get_user(record.github_username)
                        team_to_add_to: Optional[github.Team.Team] = None

                        if isinstance(
                            user,
                            github.AuthenticatedUser.AuthenticatedUser,
                        ):
                            logger(
                                f"Avoiding inviting {user.login} (yourself?)"
                            )
                            continue

                        for team in made_teams:
                            if team.name == netid_team_mapping[record.netid]:
                                team_to_add_to = team
                                break
                        if team_to_add_to is None:
                            logger(
                                "Internal error: Couldn't find team to add to"
                            )
                        else:
                            team.add_membership(user)
                            record.added_to_group = True
                            logger(f"{record.netid} added to group team")
                    except Exception:
                        logger(f"Error adding {record.netid} to group repo")
