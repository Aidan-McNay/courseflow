# Metadata

The following describes the current named metadata used across flows. New
steps should use these names when needed, and avoid introducing name
conflicts with new metadata. Only one step should ever set any given
name of metadata.

```{eval-rst}
.. py:attribute:: new_netids
   :type: list[str]

   A list of NetIDs that have just been added to the course (i.e. the flow
   has no record of them before this iteration)

   Set by: :py:class:`~canvas_steps.enrollment.AddEnrollment`

   Used by: :py:class:`~canvas_steps.enrollment.PingNewEnrollment`
```

```{eval-rst}
.. py:attribute:: old_groups
   :type: dict[str, int]

   A mapping of NetIDs to previously-assigned (but overriden) lab groups.
   This is used to know which groups have changed, to re-assign groups on
   GitHub appropriately

   Set by: :py:class:`~canvas_steps.assign_groups.AssignGroups`

   Used by: :py:class:`~github_steps.add_to_group_repos.AddToGroupRepos`
```

```{eval-rst}
.. py:attribute:: unenrolled_netids
   :type: list[str]

   A list of NetIDs that have just been dropped from the course (i.e.
   their record showed them as previously being enrolled, but they are
   no longer on Canvas)

   Set by: :py:class:`~canvas_steps.enrollment.UpdateEnrollment`
```