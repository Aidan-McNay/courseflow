# Update Steps

## Base Class

```{eval-rst}
All update steps must inherit from/implement the following base class
(with some repeated from :py:class:`~flow.flow_steps.FlowStep`)

.. autoclass:: flow.flow_steps.FlowUpdateStep()

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

   .. automethod:: update_records
```

## Implementations

```{eval-rst}
.. autoclass:: canvas_steps.enrollment.UpdateEnrollment()

   This step removes any student who is marked as enrolled, but no longer
   on Canvas. Similarly, the flow re-enrolls any record that shows the
   student as unenrolled, but the student is present on Canvas.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   Sets metadata: :py:attr:`unenrolled_netids`
```

```{eval-rst}
.. autoclass:: canvas_steps.github_usernames.GitHubUsernames()

   This step checks a Canvas quiz's responses, specifically one with a
   "Fill in the Blank" question. It gets the responses, and adds them to
   the record as their username. It additionally checks and updates the
   record with whether the GitHub username is valid (i.e. it actually
   corresponds to a GitHub profile).

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.quiz_id
      :type: int

      The ID of the Canvas quiz to check. The can be taken from the URL;
      going to the quiz, the URL should be of the form
      ``.../quizzes/<quiz_id>``

   .. py:attribute:: configs.question_id
      :type: int

      The ID of the "Fill in the Blank" question in the Canvas quiz to get
      responses from. This is slightly trickier to obtain:

      * One could determine it from the browser by inspecting the page
        source; see `here <https://community.canvaslms.com/t5/Canvas-Developers-Group/If-I-have-a-Course-ID-Quiz-ID-and-a-Question-ID-can-I-create-a/td-p/600774>`_
      * One could use the API to figure out the possible IDs (and
        corresponding names) of questions for a given quiz

      To aid with this, :py:class:`~canvas_steps.github_usernames.GitHubUsernames`
      includes the possible questions and their IDs in the exception
      thrown by an invalid question ID in ``validate``. This allows users
      to determine the question ID by initially guessing an incorrect ID,
      then inspecting the resulting exception message during validation to
      determine the correct ID.

   .. automethod:: validate

      Specifically, we make sure that a quiz with the given ID exists in
      the Canvas course, and that it contains a question with the given ID
      that is a 'Fill in the Blank' question
```

```{eval-rst}
.. autoclass:: github_steps.mark_accepted.MarkAccepted()

   This step checks the current membership of the GitHub organization, and
   marks students with usernames in the organization membership as having
   accepted their invitation.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   .. py:attribute:: configs.staff_team
      :type: str

      The name of the staff team in the GitHub organization (usually
      ``staff``). Members in this team are not considered students for the
      purpose of checking whether a student is in the organization.

   .. automethod:: validate

      Specifically, we make sure that the GitHub organization contains
      a team with the specified name
```

```{eval-rst}
.. autoclass:: utils.basic_steps.BasicUpdateStep()

   Supported record types: ``int``

   .. py:attribute:: configs.increment
      :type: int

      The amount to increment records by
   
   .. automethod:: validate

      Specifically, we make sure that the supplied increment amount is
      positive
```