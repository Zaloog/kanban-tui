# Contributing to kanban-tui

First of all, thank you for taking the time to contribute to kanban-tui!

## How can I contribute?

You can contribute to kanban-tui in many ways:

 1. [Reporting a bug][issues]
 2. Adding a new feature
 3. Fixing a bug
 4. Improving the documentation

Before starting with your PR, I recommend reaching out first by commenting on a new or existing issue,
to align on what to do.

# Setup

1. Fork the kanban-tui repository
2. Clone your forked repository
3. kanban-tui uses [uv], so make you have it installed
4. excute `uv sync --all-extras` to install all required dependencies + dev dependencies
5. kanban-tui uses [prek] for pre-commit hooks, install the hooks with `uv run prek install`
6. To check if everything works as expected run `uv run pytest` to see if all tests pass.
If you have [Make] installed you can also run `make test`


# Before opening a PR
Before opening a PR, please check the following points

- [ ] all tests pass locally
- [ ] code was formatted (should run automatically with from pre-commit hook)

<!-- Links -->
[issues]: https://github.com/Zaloog/kanban-tui/issues
[uv]: https://docs.astral.sh/uv/
[prek]: https://prek.j178.dev/
[Make]: https://en.wikipedia.org/wiki/Make_(software)
