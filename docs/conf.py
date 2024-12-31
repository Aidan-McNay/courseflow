# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("..", "pylibs").resolve()))

# Mock environment variables, so that modules can be imported
os.environ["AUTODOC_GEN"] = ""

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "cornell-canvas"
copyright = "2024, Aidan McNay"
author = "Aidan McNay"

version = "1.0.0"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_rtd_theme",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx_togglebutton",
]

templates_path = ["_templates"]
exclude_patterns = []

parametrized_on_type = {
    "flow.flow.Flow": "RecordType",
    "flow.record_storer.RecordStorer": "RecordType",
    "google_steps.spreadsheet_storer.SpreadsheetStorer": "SpreadsheetRecord",
    "flow.flow_steps.FlowRecordStep": "RecordType",
    "flow.flow_steps.FlowUpdateStep": "RecordType",
    "flow.flow_steps.FlowPropagateStep": "RecordType",
}


# Add generic parameter types (https://github.com/sphinx-doc/sphinx/issues/10568#issuecomment-2413039360)
def process_signature(
    app, what, name, obj, options, signature, return_annotation
):
    if what == "class":
        if name in parametrized_on_type:
            signature = f"[{parametrized_on_type[name]}]" + (signature or "")
    return signature, return_annotation


def setup(app):
    app.connect("autodoc-process-signature", process_signature)


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": "Aidan-McNay",  # Username/Organization
    "github_repo": "cornell-canvas",  # Repo name
    "github_version": "main",  # Version
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
}

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_favicon = "_static/img/favicon.ico"
html_css_files = ["css/code_link.css"]

html_theme_options = {
    "navigation_depth": 3,
}
