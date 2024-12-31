# Prerequisites

`courseflow` is written in Python, and was developed using
Python 3.11.9. Earlier versions may be supported, but are not
guaranteed.

`courseflow` requires the following Python prerequisites at a
baseline:

 - [`canvasapi`](https://pypi.org/project/canvasapi/) for accessing the
   Canvas LMS API
 - [`gspread`](https://pypi.org/project/gspread/) for accessing the
   Google Sheets API
 - [`PyGithub`](https://pypi.org/project/PyGithub/) for accessing the
   GitHub API
 - [`PyYAML`](https://pypi.org/project/PyYAML/) to parse YAML
   configuration files

Additional prerequisites may be considered to access different APIs. In
general, Python wrappers around APIs are preferred over direct HTTP
requests, as bearer tokens would need to be managed/wrapped anyway.

In addition to the above, `courseflow` uses the following packages
for static linting:

 - [`black`](https://pypi.org/project/black/) for formatting
 - [`flake8`](https://pypi.org/project/flake8/) for style checking,
     including the following plugins:
      - [`pydoclint`](https://pypi.org/project/pydoclint/)
      - [`flake8-annotations`](https://pypi.org/project/flake8-annotations/)
      - [`flake8-pydocstyle`](https://pypi.org/project/flake8-pydocstyle/)
 - [`mypy`](https://pypi.org/project/mypy/) for static type checking
      - This also requires [`types-PyYAML`](https://pypi.org/project/types-PyYAML/)
        for `PyYAML`'s type annotations

Future improvements will migrate formatting/style checking to
[Ruff](https://github.com/astral-sh/ruff)

```{admonition} Installing with PIP
:class: note
To install these prerequisites, users can use the provided
`requirements.txt` file:

```bash
git clone git@github.com:Aidan-McNay/courseflow.git
cd courseflow
pip install -r requirements.txt
```