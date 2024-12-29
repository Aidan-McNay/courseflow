# cornell-canvas

A framework for managing and connecting (Cornell) courses in Canvas

## Documentation

Documentation for the framework, including prerequisites, usage, and
a reference for steps/flows, can be found [here](https://aidan-mcnay.github.io/cornell-canvas/)

## Prerequisites

Scripts in this directory assume that the following environment variables
are set:

 - `CANVAS_API_KEY`: Your API token for Canvas. This can be obtained upon
     [request from Cornell](https://learn.canvas.cornell.edu/canvas-api-access-tokens/)
 - `CANVAS_API_COURSEID`: The ID of the current Canvas course. The Canvas
      URL for your course will be of the form 
      `https://canvas.cornell.edu/courses/CANVAS_API_COURSEID`
 - `GITHUB_API_KEY`: Your API token for GitHub. This can be obtained
      [from GitHub](https://github.com/settings/tokens)
 - `GMAIL_API_KEY`: Your app password for GMail. This can be obtained
      [from Gmail](https://support.google.com/accounts/answer/185833?hl=en)
 - `GOOGLE_API_JSON`: The (absolute) path to your Google service account's
      JSON credentials. The JSON file can be obtained by creating a
      [service account through Google](https://cloud.google.com/iam/docs/service-account-overview)

Not all of these will be used for all features; however, they are widely
assumed to be present.

In addition, the framework requires some Python dependencies; these can
be installed with

```bash
pip install -r requirements.txt
```

This will install both the required dependencies, as well as optional ones
used for linting.

## Directories

Contained in this directory are:

 - `pylibs`: The Python libraries/utilities used by the scripts
 - `scripts`: The main scripts for managing the course
 - `utils`: Smaller scripts for one-off runs

## Setup

To begin using the logistics scripts, first make sure that your
environment contains the above variables. In addition, make sure that the
`pylibs` directory is in your `PYTHONPATH`:

```bash
export PYTHONPATH=/path/to/pylibs:$PYTHONPATH
```

From there, you can get details on any of the scripts in the `scripts`
or `utils` directories by running:

```bash
python path/to/script.py -h
```

or simply

```bash
./path/to/script.py -h
```

In addition, scripts in the `utils` directory can be called with the `-i`
flag to gain more information about their functionality, in a pager-like
display.

## Linting
Linting of this directory can be done with the `lint` Bash script, which
performs static analysis of all Python files:

```bash
./lint
```