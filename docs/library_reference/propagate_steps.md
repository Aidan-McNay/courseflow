# Propagate Steps

## Base Class

```{eval-rst}
All propagate steps must inherit from/implement the following base class
(with some repeated from :py:class:`~flow.flow_steps.FlowStep`)

.. autoclass:: flow.flow_steps.FlowPropagateStep()

   Parent Class: :py:class:`~flow.flow_steps.FlowStep`

   .. py:property:: description
      :abstractmethod:
      :classmethod:
      :type: str

      A high-level description of the step

   .. py:property:: config_types
      :abstractmethod:
      :classmethod:
      :type: list[tuple[str, Type[ValidConfigTypes], str]]

      The types of the configurations for the step. Each tuple in the list
      should include the name, type, and description of a configuration
      (respectively). See :py:class:`~flow.flow_steps.FlowStep`

   .. py:method:: validate() -> None
      :abstractmethod:

      This function should inspect the object's ``configs`` attribute, and
      perform any static validation possible.

   .. automethod:: propagate_records
```

## Implementations

```{eval-rst}
.. autoclass:: canvas_steps.assign_groups.AssignGroups()

   This step takes in a current Canvas group
   (likely with some self-grouping), and pairs up remaining students to
   form lab groups. Groups are made to ensure that pairs are in the same
   lab section. Odd numbers are resolved by forming a group of three.

   Note that current groups are **NOT** checked to see whether they are
   groups of fewer than three; the Canvas group can be configured to
   restrict this. However, solo students in a group are removed and
   re-assigned. This also has the side-benefit that if a student drops,
   the remaining partner is re-assigned to another group automatically.
   If an instructor wishes to disable this, they should disable the
   step.

   The Canvas group (as well as our records) will be updated with the new
   group mapping.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   Sets metadata: :py:attr:`old_groups`
```

```{eval-rst}
.. autoclass:: canvas_steps.enrollment.PingNewEnrollment()

   This step uses Gmail to send an email to a configured recipient, informing
   them that new enrollment in the course has occurred.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   Uses metadata: :py:attr:`new_netids`

   .. py:attribute:: configs.send_email
      :type: str

      The email to send from (matching ``GMAIL_API_KEY``)

   .. py:attribute:: configs.recv_email
      :type: str

      The email to send the notification to

   .. py:attribute:: configs.subject
      :type: str

      The subject that the notification email should have
```

```{eval-rst}
.. autoclass:: github_steps.add_to_group_repos.AddToGroupRepos()

   This step uses a configured group name format to create a GitHub team for
   the group. Access to the group repository is managed through access to
   this team. As group membership changes, access to the GitHub teams is
   updated as well.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   Uses metadata: :py:attr:`old_groups`

   .. py:attribute:: configs.name_format
      :type: str

      The format to use for naming GitHub teams. Instances of ``<num>`` will
      be replaced with the group's number.

   .. py:attribute:: configs.num_places
      :type: int

      The minimum number of places to represent the group's number with
      (filling with zeros as necessary). For example, if set to 2,
      Group 6 would have their number formatted as ``06`` in their team name.
```

```{eval-rst}
.. autoclass:: github_steps.add_to_personal_repos.AddToPersonalRepos()

   This step checks for students that have a personal repo (indicated by
   having a personal repo name), but don't currently have access, and
   provides them access.

   Supported record types: :py:class:`~records.student_record.StudentRecord`
```

```{eval-rst}
.. autoclass:: github_steps.create_group_repos.CreateGroupRepos()

   This step checks for records that have a group number but no repo yet,
   and creates the appropriate repos with a README file.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.name_format
      :type: str

      The format to use for naming GitHub teams. Instances of ``<num>`` will
      be replaced with the group's number.

   .. py:attribute:: configs.num_places
      :type: int

      The minimum number of places to represent the group's number with
      (filling with zeros as necessary). For example, if set to 2,
      Group 6 would have their number formatted as ``06`` in their team name.

   .. py:attribute:: configs.readme_path
      :type: str

      The path to the local README file, to include in the repo.
      Instances of ``<repo_name>`` will be replaced appropriately.

   .. py:attribute:: configs.readme_commit_msg
      :type: str

      The commit message to use when adding the README

   .. py:attribute:: configs.create_upstream
      :type: bool

      Whether to create a branch of the repo named ``upstream``

   .. py:attribute:: configs.staff_team
      :type: str

      The name of the staff team in the GitHub organization. The team will
      be given access to all created repos.

   .. py:attribute:: configs.staff_permissions
      :type: str

      The permissions to give the staff team in all created repos
      (any of ``pull``, ``triage``, ``push``, ``maintain``, or ``admin``)
```

```{eval-rst}
.. autoclass:: github_steps.create_personal_repos.CreatePersonalRepos()

   This step checks for records that don't have a repo corresponding to
   their NetID, and creates a repo for them.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.name_format
      :type: str

      The format to use for naming GitHub teams. Instances of ``<netid>``
      will be replaced with the student's NetID.

   .. py:attribute:: configs.readme_path
      :type: str

      The path to the local README file, to include in the repo.
      Instances of ``<repo_name>`` will be replaced appropriately.

   .. py:attribute:: configs.readme_commit_msg
      :type: str

      The commit message to use when adding the README

   .. py:attribute:: configs.create_upstream
      :type: bool

      Whether to create a branch of the repo named ``upstream``

   .. py:attribute:: configs.staff_team
      :type: str

      The name of the staff team in the GitHub organization. The team will
      be given access to all created repos.

   .. py:attribute:: configs.staff_permissions
      :type: str

      The permissions to give the staff team in all created repos
      (any of ``pull``, ``triage``, ``push``, ``maintain``, or ``admin``)
```

```{eval-rst}
.. autoclass:: github_steps.invite_students.InviteStudents()

   This step checks for students that have a valid GitHub username, and
   invites them to join the GitHub organization.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.student_team
      :type: str

      The name of the student team on GitHub. All students will be invited
      to join this team.
```

```{eval-rst}
.. autoclass:: github_steps.remove_unenrolled.RemoveUnenrolled()

   This step checks for records that have been sent an invite but are
   no longer enrolled, and removes them from GitHub.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.staff_team
      :type: str

      The name of the staff team on GitHub, to sanity-check that we never
      remove a staff member
```

```{eval-rst}
.. py:class:: github_steps.tag_repo.RepoTagger()

   A propagate step to tag a specific lab submission.

   This step is generated for a specific lab submission and repo type
   (``personal`` or ``group``), and will tag repos of the specified type
   with the given tag.

   Supported record types: :py:class:`~records.tag_record.TagRecords`

   .. admonition:: Generating :py:class:`~github_steps.tag_repo.RepoTagger`\ s
      :class: note

      :py:class:`~github_steps.tag_repo.RepoTagger`\ s are unlike other steps
      in that they are not statically defined. Instead, a dynamic type is
      created using :py:func:`~github_steps.tag_repo.get_tagger` to tag
      a specific repo type for a specific lab submission. See
      :py:func:`~github_steps.tag_repo.get_tagger` for more details on how
      to generate :py:class:`~github_steps.tag_repo.RepoTagger`\ s

   .. py:attribute:: configs.tag_name
      :type: str

      The tag name that will be used to tag the repos

   .. py:attribute:: configs.deadline
      :type: datetime.datetime

      The deadline for the lab. Repos will be tagged when this step is run
      on or after the deadline.
```

```{eval-rst}
.. autoclass:: utils.basic_steps.BasicPropagateStep()

   Supported record types: ``int``
```

```{eval-rst}
.. autoclass:: utils.ping_invalid_username.PingInvalidUsername()

   This step finds the records that submitted an invalid GitHub username,
   and emails them informing them of such.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.start_date
      :type: datetime.datetime

      The date when email notifications should start (none will be sent
      before this date)

   .. py:attribute:: configs.email_gap
      :type: int

      The number of days to wait between notifications.

   .. py:attribute:: configs.email_template
      :type: str

      The path to a template email (in the form of a text file).
      Instances of ``<first_name>``, ``<last_name>``, and ``<username>``
      will be replaced appropriately for each notification.
   
   .. py:attribute:: configs.send_email
      :type: str

      The email to send from (matching ``GMAIL_API_KEY``)

   .. py:attribute:: configs.subject
      :type: str

      The subject that the notification email should have
```

```{eval-rst}
.. autoclass:: utils.ping_no_accept.PingNoAccept()

   This step finds records that have a pending invitation (that they
   haven't accepted), and emails them informing them of such.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.start_date
      :type: datetime.datetime

      The date when email notifications should start (none will be sent
      before this date)

   .. py:attribute:: configs.email_gap
      :type: int

      The number of days to wait between notifications.

      (Note that this gap is also adhered to from when the invitation
      was initially sent).

   .. py:attribute:: configs.email_template
      :type: str

      The path to a template email (in the form of a text file).
      Instances of ``<first_name>``, ``<last_name>``, and ``<username>``
      will be replaced appropriately for each notification.
   
   .. py:attribute:: configs.send_email
      :type: str

      The email to send from (matching ``GMAIL_API_KEY``)

   .. py:attribute:: configs.subject
      :type: str

      The subject that the notification email should have
```

```{eval-rst}
.. autoclass:: utils.ping_no_username.PingNoUsername()

   This step finds records that have no GitHub username (a.k.a. they
   haven't submitted one yet), and emails them informing them of such.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.start_date
      :type: datetime.datetime

      The date when email notifications should start (none will be sent
      before this date)

   .. py:attribute:: configs.email_gap
      :type: int

      The number of days to wait between notifications.

   .. py:attribute:: configs.email_template
      :type: str

      The path to a template email (in the form of a text file).
      Instances of ``<first_name>`` and ``<last_name>``
      will be replaced appropriately for each notification.
   
   .. py:attribute:: configs.send_email
      :type: str

      The email to send from (matching ``GMAIL_API_KEY``)

   .. py:attribute:: configs.subject
      :type: str

      The subject that the notification email should have
```
