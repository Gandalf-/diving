# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands
- Full test suite: `make test`
- Unit tests only: `python3 -m unittest`
- Single test: `python3 -m unittest test.test_module`
- Integration tests: `bash test/integration.sh`
- JavaScript tests: `make jstest` or `jasmine --config=.jasmine.mjs`
- Type checking: `mypy .`
- Linting: `ruff check --fix .`
- Formatting: `ruff format *.py */*.py`

## Development Workflow
- Local build: `make local` or `make fast` (skips expensive operations)
  - Outputs to `~/working/object-publish/diving-web/`
- Development mode: `make dev` (auto-rebuild on file changes using entr)
- Serve locally: `make serve` (serves from ~/working/object-publish/diving-web)
- Clean: `make clean` (removes generated HTML)

### JavaScript Development
- Source files in `web/` directory are copied to output during build
- Detective game: `web/game.js` → `detective/game.js` (versioned)
- Changes to `web/*.js` require running `make local` to regenerate output
- Integration test outputs to `~/working/tmp/diving` but doesn't test JavaScript functionality
- JavaScript unit tests: Uses Jasmine to test pure functions in `web/*.js` files
  - Test files: `web/search.spec.js`, `web/game.spec.js`
  - Run with: `make jstest` (included in `make test`)
  - Pure functions are exported via CommonJS for testing while maintaining browser compatibility

## Architecture Overview

This is a static site generator for a scuba diving photography website. The codebase processes diving photos organized by date and location, generates taxonomy-based galleries, and produces HTML pages with Wikipedia integration.

### Data Flow
1. **Input**: Images in `~/Pictures/diving/` organized as `YYYY-MM-DD - [Location]/[files]`
2. **Database**: Uses `apocrypha-server` (key-value store) for caching image metadata, hashes, and Wikipedia information
3. **Processing**: `util/runner.sh` generates image/video thumbnails and fullsize versions via ImageMagick/FFmpeg
4. **Generation**: `gallery.py` is the main entry point that produces HTML pages
5. **Output**: Static HTML files in `~/working/object-publish/diving-web/`

### Key Modules
- **gallery.py**: Main entry point; orchestrates HTML generation for taxonomy, sites, timeline, and detective pages
- **hypertext.py**: HTML generation utilities; defines page types (Gallery, Taxonomy, Sites, Timeline, Detective)
- **information.py**: Wikipedia integration for species information
- **timeline.py**: Chronological dive log pages
- **detective.py**: Identification quiz game
- **locations.py**: Dive site categorization and regions
- **search.py**: Search index generation
- **util/database.py**: Interface to apocrypha-server (RealDatabase) and TestDatabase for testing
- **util/translator.py**: Latin/Greek scientific name translation to English
- **util/taxonomy.py**: Biological taxonomy tree management
- **util/image.py**: Image metadata and path handling
- **util/collection.py**: Tree data structure utilities for organizing images hierarchically
- **util/runner.sh**: Bash script for parallel image/video processing (thumbnails, conversions)

### Data Files
- **data/taxonomy.yml**: Biological taxonomy mappings
- **data/static.yml**: Configuration (dive locations, categories, pinned images, ignored terms)
- **data/translations.yml**: Latin/Greek to English translations (auto-generated via `util/translator.py`)
- **data/db.json**: apocrypha database file (image cache, Wikipedia data)

### Database Requirement
Most operations require `apocrypha-server` to be running. The server is auto-started by `util/macos.sh` and `test/integration.sh` scripts. Direct usage: `apocrypha-server --headless --database data/db.json`

## Code Style Guidelines
- Code should be clear, concise, and obvious; avoid extraneous comments
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
