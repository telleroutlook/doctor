# Repository Guidelines

## Project Structure & Module Organization
- The `code/` directory holds the Python application: `main.py` coordinates crawler, API, and search flows while subpackages (`crawler/`, `parsers/`, `processors/`, `database/`, `config/`) contain the specialized logic described in `code/README.md`.
- Supporting data and configs live under `code/data/`, `code/config/`, and `code/database/`; keep generated artifacts (output, logs) outside the source tree or under a dedicated `tmp/` folder when experimenting.
- Reference documentation and analysis reports stay in `docs/` (screenshots, architecture notes, site analyses) to keep implementation and research clearly separated.

## Build, Test, and Development Commands
- `pip install -r code/requirements.txt`: install all required Python libraries before running any commands.
- `python code/main.py setup-db`: create or refresh the database schema before crawling or serving results.
- `python code/main.py crawl --language <lang> --version <edition> [--max-pages N]`: run the scraper, specifying `--output` when you need a custom folder; reuse `--max-pages` for bounded development runs.
- `python code/main.py api` / `python code/main.py search`: launch the Flask API or search UI locally for manual verification.
- `python code/main.py test` and `pytest code/test_crawler.py`: execute the pytest suite; prefer `pytest code/test_crawler.py::test_xxx` when targeting a single case.

## Coding Style & Naming Conventions
- Python files follow four-space indentation; prefer descriptive snake_case for functions/variables and PascalCase for classes defined under `crawler/`, `processors/`, and `database/`.
- Keep logging consistent with `loguru` (imported across modules) and centralize configuration values in `config/` or `main.py` so crawlers remain parameterized.
- There is no enforced formatter tracked, so format new code with a Black-style mindset (line length ~88, trailing commas for long literals) and run `python -m compileall` or `pytest` to catch syntax issues before committing.

## Testing Guidelines
- Tests rely on `pytest` (see `code/requirements.txt`); all test files start with `test_` and individual cases begin with `test_` for automatic discovery.
- Use fixtures sparingly; prefer small, deterministic inputs to keep crawlers reproducible.
- Run `python code/main.py test` as a quick smoke check, then `pytest code/test_crawler.py` for deeper verification before marking work done.

## Commit & Pull Request Guidelines
- This repository does not currently include a Git history, so adopt a Conventional Commits style (`feat(crawler): add incremental retry`) when creating the initial commits.
- PRs should summarize scope, list executed commands (crawl/test), link relevant issue/analysis doc from `docs/`, and include sample output or screenshots for UI/story changes.
- Mention any manual steps (DB setup, translation updates) inside the PR description so reviewers can reproduce the change.

## Security & Configuration Tips
- Review `docs/爬虫策略与数据库架构设计.md` before modifying crawlers to keep compliance with robots.txt and database locking strategies.
- Keep secrets out of the repo; populate credentials via environment variables or `python-dotenv` files referenced in `config/` rather than committing them.
