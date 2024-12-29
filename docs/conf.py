# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cornell-canvas'
copyright = '2024, Aidan McNay'
author = 'Aidan McNay'

version = '1.0.0'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_rtd_theme", "myst_parser", "sphinxcontrib.wavedrom"]

templates_path = ["_templates"]
exclude_patterns = []



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
