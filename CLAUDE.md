# CLAUDE.md

Static site generator for a scuba diving photography website. Processes photos organized by
date/location into taxonomy-based galleries with Wikipedia integration.

## Commands
```bash
make test          # Full test suite (unit + integration + JS)
make local         # Build site to ~/working/object-publish/diving-web/
make fast          # Quick rebuild (skips unchanged media)
make lint          # mypy + ruff + shellcheck
make format        # isort + ruff format
```

## Entry Points
- `cli.py` - Unified CLI for all operations
  - `cli.py generate [image_root]` - Build the website
  - `cli.py imprecise --list|--find|--update` - Manage imprecise species names
  - `cli.py missing --missing|--incomplete` - Find taxonomy gaps

## Project Structure
```
cli.py                    # Main entry point
diving/
  generate.py             # Site generation orchestration
  gallery.py              # HTML generation for galleries/taxonomy/sites
  hypertext.py            # HTML utilities, page types (Gallery, Taxonomy, Sites, Timeline)
  detective.py            # Species ID quiz game
  timeline.py             # Chronological dive logs
  locations.py            # Dive site regions
  information.py          # Wikipedia integration
  imprecise.py            # Imprecise name detection/correction
  missing.py              # Missing taxonomy detection
  macos.sh                # Build orchestration (start db, run media + generate)
  media.sh                # Image/video processing (ImageMagick, ffmpeg)
  util/
    taxonomy.py           # Scientific name mappings
    collection.py         # Image tree structures
    image.py              # Image metadata/paths
    database.py           # apocrypha-server interface
    ...                   # Many other utility modules
data/
  taxonomy.yml            # Species → scientific name mappings
  static.yml              # Dive sites, categories, pinned images
  db.json                 # Cache (hashes, Wikipedia data)
web/                      # Static JS/CSS assets
```

## Data Flow
1. Images in `~/Pictures/diving/YYYY-MM-DD - Location/`
2. `media.sh` generates thumbnails/fullsize via ImageMagick/ffmpeg
3. `generate.py` builds HTML pages using `gallery.py`
4. Output to `~/working/object-publish/diving-web/`

## Database
Most operations require `apocrypha-server`. Auto-started by `macos.sh` and `test/integration.sh`.

## Code Style
- Single quotes, 100 char lines, type annotations required
- Enforced by ruff/mypy via `make format` and `make lint`
