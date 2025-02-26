# Diving Codebase Commands & Guidelines

## Build & Test Commands
- Full test suite: `make test`
- Unit tests only: `python3 -m unittest`
- Single test: `python3 -m unittest test.test_module`
- Integration tests: `bash test/integration.sh`
- Type checking: `mypy .`
- Linting: `ruff check --fix .`
- Formatting: `ruff format *.py */*.py`

## Code Style Guidelines
- Single quotes for strings: `'example'`
- Maximum line length: 100 characters
- Type annotations required for all functions
- Import order: stdlib, third-party, local modules
- Error handling: use asserts for internal logic, explicit exceptions with messages
- Class naming: PascalCase (e.g., `DiveInfo`)
- Function/variable naming: snake_case (e.g., `dive_info_html`)
- Constants: UPPER_SNAKE_CASE (e.g., `_XML_NS`)
- Document functions with docstrings using triple double-quotes
- Use type aliases (e.g., `Tree = Any`) for complex types