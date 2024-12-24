"""Sets common variables and drivers for the Canvas course.

Required environment variables:
 - GITHUB_API_KEY: Your API key for accessing GitHub
"""

import github
import os

# The GitHub organization name
_name = "cornell-ece2300"

# Access to the GitHub API
_token = github.Auth.Token(os.environ["GITHUB_API_KEY"])
_github = github.Github(auth=_token)

# The specific organization for the class
_org = _github.get_organization("cornell-ece2300")
