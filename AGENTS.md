# Repository Guidelines

## Project Structure & Module Organization

- `src/vibe_coding/` is the installed package, built with the `uv_build` backend from a `src/` layout. `src/vibe_coding/calc/` holds the `Calculator` implementation, re-exported up to the top-level package.
- `main.py` at the repo root is a standalone script *outside* the package. The `vibe-coding` console script resolves to `vibe_coding:main` instead — see `CLAUDE.md` for why the two differ.
- `tests/` holds the pytest suite, currently `tests/test_calculator.py`.
- `pyproject.toml` contains project metadata, the Python version requirement (`>=3.13`), and dependencies.
- `README.md` is reserved for user-facing setup and usage notes. `CLAUDE.md` records repository-level agent context.

## Build, Test, and Development Commands

This project is managed with [uv](https://docs.astral.sh/uv/) and builds via the `uv_build` backend.

- `uv sync` installs dependencies into `.venv`.
- `uv run pytest` runs the test suite; `uv run pytest tests/test_calculator.py::test_add` runs a single test.
- `uv run python main.py` runs the root script; `uv run vibe-coding` runs the packaged console-script entry point. These are two different functions.

Prefer `uv run …` over bare commands — no `[tool.*]` configuration exists in `pyproject.toml`, so `pytest` only resolves the `vibe_coding` import when `.venv` is already activated.

When adding dependencies, update `pyproject.toml` (uv will refresh `uv.lock`) and document the installation/run workflow in `README.md`. Add explicit lint commands here when that tooling is introduced.

## Coding Style & Naming Conventions

Use standard Python conventions: four spaces for indentation, UTF-8 source files, `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_CASE` for constants. Prefer small functions with descriptive names and type hints for public or non-obvious interfaces. Keep imports at the top of files and protect executable scripts with `if __name__ == "__main__":`.

No formatter or linter is configured. Do not claim automated formatting is enforced until a tool is added to the project configuration.

## Testing Guidelines

Tests run on `pytest` (declared in `[project] dependencies`, so `uv sync` installs it). There is no coverage requirement. Add tests alongside the implementation in the top-level `tests/` directory, following `tests/test_calculator.py`: one `test_<behavior>` function per case, and Korean docstrings to match the existing suite. Use `pytest.raises` for expected-error cases, as `test_divide_by_zero` does.

## Commit & Pull Request Guidelines

The repository has no commit history, so no established commit convention exists. Use concise, imperative commit subjects, for example `Add greeting CLI option`. Keep commits focused. Pull requests should explain the change and verification performed, link relevant issues when available, and include screenshots or sample output for visible behavior changes.
