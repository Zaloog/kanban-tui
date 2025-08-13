# Contributing to kanban-tui

First of all, thanks for taking the time to contribute to kanban-tui!

## How can I contribute?

You can contribute to kanban-tui in many ways:

 1. [Report a bug][issues]
 2. Add a new feature
 3. Fix a bug
 4. Improve the documentation

# Setup

1. Fork the kanban-tui repository
2. Clone your forked repository
3. kanban-tui uses [uv], so make you have it installed
4. excute `uv sync --all-extras` to install all required dependencies + dev dependencies
5. kanban-tui uses [pre-commit], install the hooks with `uv run pre-commit install`
6. To check if everything works as expected run `uv run pytest` to see if all tests pass.
If you have [Make] installed you can also run `make test`


# Before opening a PR
Before opening a PR, please check the following points

- [ ] all tests pass locally
- [ ] code was formatted (should run automatically with from pre-commit hook)

<!-- Links -->
[issues]: https://github.com/Zaloog/kanban-tui/issues
[uv]: https://docs.astral.sh/uv/
[pre-commit]: https://pre-commit.com/
[Make]: https://en.wikipedia.org/wiki/Make_(software)
