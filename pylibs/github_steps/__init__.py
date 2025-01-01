"""Sets common variables and drivers for the Canvas course.

Required environment variables:
 - GITHUB_API_KEY: Your API key for accessing GitHub
 - GITHUB_ORG: The organization to access
"""

import github
import os
from typing import cast

if "AUTODOC_GEN" in os.environ:
    _name = cast(str, object())
    _token = cast(github.Auth.Token, object())
    _github = cast(github.MainClass.Github, object())
    _org = cast(github.Organization.Organization, object())
else:
    # The GitHub organization name
    _name = os.environ["GITHUB_ORG"]

    # Access to the GitHub API
    _token = github.Auth.Token(os.environ["GITHUB_API_KEY"])
    _github = github.Github(auth=_token)

    # The specific organization for the class
    _org = _github.get_organization(_name)
