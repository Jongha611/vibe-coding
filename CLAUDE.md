# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This is a [uv](https://docs.astral.sh/uv/) project (uv 0.11.7, Python 3.13). Prefer `uv run …`
for everything — `pyproject.toml` declares no `[tool.*]` sections, so a bare `pytest` resolves
the `vibe_coding` import only when `.venv` is already activated.

```bash
uv sync                                          # install dependencies
uv run pytest                                    # run the full suite
uv run pytest tests/test_calculator.py::test_add # run a single test
uv run pytest -q -k divide                        # run tests matching a name
```

`pytest` is declared in `[project] dependencies` rather than a dev-dependency group, so
`uv sync` alone is enough to make the suite runnable.

## Two entry points — they are not the same

`main()` is defined twice, in unrelated places, and the console script does **not** run the
one at the repo root:

| Command | Runs | Output |
|---|---|---|
| `uv run python main.py` | root `main.py` | `Hello from vibe-coding!` |
| `uv run vibe-coding` | `vibe_coding:main`, per `[project.scripts]` | `vibe-coding = vibe_coding:main` |

Root `main.py` lives outside `src/`, so it is not part of the installed package and is
unreachable from the `vibe-coding` command. When changing CLI behavior, confirm which of the
two you actually mean.

## Architecture

The package uses a `src/` layout built by the `uv_build` backend. `Calculator` is re-exported
twice so that consumers import it from the top-level package:

```
src/vibe_coding/calc/calculator.py   defines Calculator
src/vibe_coding/calc/__init__.py     re-exports it
src/vibe_coding/__init__.py          re-exports it again  ->  from vibe_coding import Calculator
```

`tests/test_calculator.py` relies on that flat path. **Adding a new module means threading it
through both `__init__.py` files** and their `__all__` lists, or it won't be reachable the way
existing code expects.

## Conventions

- Test docstrings are written in Korean (e.g. `"""더하기 테스트"""`). Match this in new tests.
- `Calculator` methods have no type hints. Don't add them to isolated methods — either leave
  the existing style alone or convert the class as a deliberate change.
- No formatter or linter is configured. Do not describe formatting as enforced.

## Repository state

Nothing is committed yet — there is no git history, so no commit convention is established.
`README.md` is currently empty.
