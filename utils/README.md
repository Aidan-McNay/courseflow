# utils

This directory contains smaller scripts for gathering
interesting data about the course and what's going on, as well as 
performing one-off actions.

## Current Scripts

The current utility scripts include:

 - `group-section-check.py`: Check that all groups in a given category on
     Canvas contain students in the same lab section
 - `pull-assignment.py`: Pulls data about the current grading status of an
     assignment to a spreadsheet
 - `tag-integrity-check.py`: Chach that no tags have been messed with for
     a given lab, using the collected hashes in `TagRecord`s

## Running

To run a script, you can run

```bash
python path/to/script.py -h
```

or simply

```bash
./path/to/script.py -h
```

The script will tell you information about what it does and any arguments
it needs