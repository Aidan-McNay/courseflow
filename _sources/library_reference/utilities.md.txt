# Utilities

In addition to the flow framework, `courseflow` includes one-off scripts
for performing actions with the available APIs that may be useful to
course instructors. These scripts can be found in the `utils` directory.

All of these scripts will show their usage when run with the `-h` flag.
In addition, to print more verbose instructions detailing the script and
how it should be used, users could use the `-i` flag.

<hr style="border:2px solid #2980b9">

## `group-section-check`

`group-section-check` is used to ensure that, for a given group category,
all groups consist only of students in the same lab section. This is to
ensure that students haven't accidentally signed up to be in a lab group
with someone from a different lab (and can also be used to verify
lab groupings).

```{eval-rst}
.. attribute:: category
   :no-index:

   The group category on Canvas to check for lab section homogeneity
```

`group-section-check` uses the Canvas sections to check for section
homogeneity, and assumes that a section corresponds to a lab section if
and only if the section name contains 'LAB' (as is the case at time of
writing for sections populated by Cornell). If this ever becomes not the
case, please modify the assignment to `lab_sections`. Future versions of
the script might take in a regex to identify lab sections, if needed.

<hr style="border:2px solid #2980b9">

## `init-course`

`init-course` is used to initialize a Canvas course with various
components, including assignments, quizzes, and student groups. This
allows instructors to expedite the setup of recurring offerings, as well
as to configure the course in a text-based, reproducible format.

```{eval-rst}
.. attribute:: attributes
   :no-index:

   The YAML file specifying the attributes/components to initialize the
   Canvas course with

.. attribute:: reset
   :no-index:

   Whether to reset/wipe the current course attributes before adding the
   specified attributes
```

`init-course` takes in a YAML file with specifications of the various
course components to initialize the course from. See the documentation
and the example attribute file for examples.

Note that additional configurations may be necessary (such as the
creation of rubrics and their mapping to assignments). This is not
included, due to the difficulty of representation in a YAML file;
instead, other utilities should be used for their creation.

In addition, `init-course` allows a user to reset the course,
specifically any previously-made attributes (assignments, assignment
groups, group categories, and quizzes). This can be used to wipe any
pre-existing content (in order to start from a blank slate). Resetting
the course, along with providing an initialization file, will result in
a course with the same attributes. However, wiped content cannot be
(easily) retrieved, and should therefore be used cautiously.
`init-course` will prompt for confirmation whenever using this feature,
even if run silently.

An example configuration file is shown below as a syntax reference:

```{eval-rst}
.. code-block:: yaml
   :class: toggle

   # ========================================================================
   # An example attribute file to initialize a course with
   # ========================================================================
   # Author: Aidan McNay
   # Date: December 29th, 2024
   
   # ------------------------------------------------------------------------
   # Assignment Groups
   # ------------------------------------------------------------------------
   
   assignment_groups:
    - name: "Quizzes"
      weight: 10
    - name: "Labs"
      weight: 25
   
   # ------------------------------------------------------------------------
   # Group Categories
   # ------------------------------------------------------------------------
   
   group_categories:
    - name: "Lab 1 Report Groups"
    - name: "Lab 2 Report Groups"
      self_signup: "enabled"
   
   # ------------------------------------------------------------------------
   # Assignments
   # ------------------------------------------------------------------------
   
   assignments:
    - name: "Lab 1 Report"
      description: "The Canvas Assignment for the Lab 1 Report"
      assignment_group: "Labs"
      submission_types: "online_upload"
      allowed_extensions:
       - "docx"
       - "pdf"
      grading_type: "points"
      points_possible: 5.25
      group_category: "Lab 1 Report Groups"
      published: True
   
    - name: "Lab 2 Report"
      description: "The Canvas Assignment for the Lab 2 Report"
      assignment_group: "Labs"
      submission_types: "online_upload"
      allowed_extensions:
       - "pdf"
      grading_type: "points"
      points_possible: 5.25
      group_category: "Lab 2 Report Groups"
      published: False
      due_at: 2024-12-24 11:59:00
      unlock_at: 2024-12-09 11:59:00
      lock_at: 2024-12-26 11:59:00
   
   # ------------------------------------------------------------------------
   # Quizzes
   # ------------------------------------------------------------------------
   
   quizzes:
    - title: "GitHub Username Form"
      description: >-
        We will be using GitHub to distribute and grade the lab assignments. 
        Students will also be using GitHub to collaborate with their lab
        partner on lab assignments. In order to invite students to the
        course's GitHub organization we need to know your NetID and your
        GitHub username.
   
   
        <b>NOTE</b>: We do NOT use the Cornell GitHub. We use the public
        github.com system which means you need to explicitly have an account
        on github.com. If you do not already have a GitHub account, go to
        https://github.com/join. Make sure you use your netid@cornell.edu
        email address if you are creating a new account. Your NetID makes a
        good GitHub username.
      quiz_type: "graded_survey"
      assignment_group: "Quizzes"
      published: True
      allowed_attempts: -1
      questions:
       - name: "GitHub Username"
         text: "GitHub Username:"
         type: "short_answer_question"
         points_possible: 0
```

<hr style="border:2px solid #2980b9">

## `tag-integrity-check`

`tag-integrity-check` is used to check that all staff-tagged repos are
intact. The repo tags are checked against stored checksums to ensure that
no manipulation has occurred since the course staff tagged them.

```{eval-rst}
.. attribute:: lab
   :no-index:

   The lab submission to check for integrity (i.e. a name in the
   :py:class:`~records.tag_record.TagRecords`\ 's ``labs`` attribute)

.. attribute:: sheet_id
   :no-index:

   The ID of the Google Sheet where :py:class:`~records.tag_record.TagRecords`
   are stored

.. admonition:: Service Account access
   :class: note

   Make sure that your service account has access to the Google Sheet
   with this ID!

.. attribute:: tab
   :no-index:

   The tab on the Google Sheet to get :py:class:`~records.tag_record.TagRecords`
   from

``tag-integrity-check`` takes the expected tags from a Google Sheet, and
assumes that the sheet represents a collection of
:py:class:`~records.tag_record.TagRecords` as stored by a 
:py:class:`~google_steps.spreadsheet_storer.SpreadsheetStorer`. Using
those records, the script will check not only that the tags are present,
but that the hashes of the tag and the commit that it points to are as
expected.
```

<hr style="border:2px solid #2980b9">

## `upload-grades`

`upload-grades` is used to populate the grades for a Canvas assignment
based on a Google Sheet. Any information that was already part of the
Canvas assignment (including preexisting grades and/or comments) will be
deleted; the Google Sheet should be the ground truth for grades.

```{eval-rst}
.. attribute:: assignment
   :no-index:

   The Canvas assignment to upload grades for

.. attribute:: delete_comments
   :no-index:

   If supplied, ``upload-grades`` will delete pre-existing comments on
   submissions for the assignment

.. attribute:: sheet_id
   :no-index:

   The ID of the Google Sheet to access

.. admonition:: Service Account access
   :class: note

   Make sure that your service account has access to the Google Sheet
   with this ID!

.. attribute:: tab
   :no-index:

   The tab/worksheet of the Google Sheet to get the grades from
```

`upload-grades` will iterate through the rows of the spreadsheet until
it finds one containing `Grade`. It will assume that these are the
appropriate column headers, and will interpret all further rows as grade
submissions. Such headers can be hidden if desired for sheet aesthetics.

The following headers should be present:
 - `Grade`: The final grade for the assignment
 - `NetID`: The NetID of the student to be graded (individual assignment)
     __*OR*__ the name of the group to be graded (group assignment)
 - `Comment`: (Optional) A comment to attach with the submission
 - `<rubric-criterion-name>`: For each criterion in the rubric attached
     to the assignment (if any), we expect a column with the exact
     criterion name, indicating the score for the criterion

Lastly, `upload-grades` assumes that the grading scheme for the assignment
on Canvas is either `Points` or `Letter Grade`, and will cast values under
the `Grade` column as appropriate. Further grading schemes can be supported
by modifying the `cast_to_grade` function as appropriate.