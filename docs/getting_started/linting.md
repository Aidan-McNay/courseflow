# Linting

`cornell-canvas` is often run on sensitive student data; as such, we want
to perform as many checks on our code ahead of time as we can to have
confidence in its correctness. This includes running steps initially in
debug mode, but also having support for static-time analysis of our code,
which our linter performs. This includes:

 - Formatting with Black
 - Style checking with Flake8
 - Type checking with Mypy

Flake8 extensions, as well as the `--strict` flag for Mypy, are used to
robustly check our code. These can all be run using the top-level `lint`
script.