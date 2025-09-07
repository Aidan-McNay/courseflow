# ece6745_2025s

A collection of `courseflow` utilities for the 2025 spring offering of ECE 6745.

## Files

This directory includes:

 - `ece6745_manager.py`: A top-level manager for ECE 6745's flows. This is
   intended to be the main script run to manage ECE 6745, and should be
   scheduled using something like `cron` or `systemd`
 - `init-course.yaml`: An attributes list, to initialize the course with
   the `init-course` utility
 - `flows`: The flows used by ECE 6745
 - `configs`: The configurations for ECE 6745's flows
 - `templates`: Various text templates, to be used by ECE 6745's flows