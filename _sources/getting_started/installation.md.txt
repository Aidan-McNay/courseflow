# Installation

`courseflow` isn't currently available as a package through PyPI.
Instead, users should locally clone the repository to set up the
framework. It is encouraged that developers make in-place extensions,
such that they could later be merged upstream for others to use

## Local Setup

To set up locally, all that's required is to have a local clone of the
repository, with the `pylibs` directory in the `PYTHONPATH` variable:

```bash
git clone git@github.com:Aidan-McNay/courseflow.git
cd courseflow

# Include `pylibs` in our Python path
export PYTHONPATH="$PWD/pylibs:$PYTHONPATH"
```

For repeated use, users may wish to add the last line to their `.bashrc`
or equivalent (making the prepended directory absolute).

## Environment Variables

`courseflow` assumes that the following environment variables are used
to provide access to API keys, as well as identify the relevant course:

 - `CANVAS_API_KEY`: Your [Canvas developer key](https://canvas.instructure.com/doc/api/file.developer_keys.html),
     to gain access to Canvas endpoints. For Cornell, these can be
     requested through CTI by going to _Account_ on the left-hand panel,
     the navigating to _Settings -> New Access Token_
 - `CANVAS_API_COURSEID`: The ID of the relevant Canvas course (usually a
     five-digit number). If you go to the webpage of your Canvas course,
     the URL should end with `.../courses/<COURSEID>`
 - `GITHUB_API_KEY`: Your [(classic) GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
     to gain access to GitHub endpoints. Note that many of the endpoints
     require you to have administrator access to the relevant organization
 - `GITHUB_ORG`: The name of the GitHub organization to use for
     GitHub-based steps
 - `GMAIL_API_KEY`: Your [Google app password](https://support.google.com/mail/answer/185833?hl=en),
     to gain access to your GMail account.
 - `GOOGLE_API_JSON`: The (absolute) path to your
     [Google service account JSON credentials](https://cloud.google.com/iam/docs/keys-create-delete#creating),
     allowing access to your service account. See the link for more
     details on how to create a service account and obtain the JSON key.
     This is used currently to access spreadsheets through `gspread`; you
     will accordingly need to share any Google Sheets you want to access
     with the service account

Future improvements will migrate GMail access to OAuth2.0, likely through
a wrapper like [`google-workspace`](https://github.com/dermasmid/google-workspace),
additionally unifying the access mechanism with spreadsheets through
`gspread`.

```{admonition} Key Usage
:class: note
It is not necessary to have all of the above keys to use the framework;
keys will be checked for as necessary on import, and a `KeyError` will
be thrown if the variable isn't present.
```