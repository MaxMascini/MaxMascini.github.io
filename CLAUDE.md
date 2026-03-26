# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal portfolio and blog website ("MinMaxed") for Max Mascini, built with [Quarto](https://quarto.org/) and hosted on GitHub Pages. Content is written in `.qmd` (Quarto Markdown) files; code blocks (Python/Jupyter) are executed at render time and frozen.

## Commands

```bash
# Render the full site locally (outputs to _site/)
quarto render

# Preview with live reload
quarto preview

# Render a single file
quarto render path/to/file.qmd

# Install Python dependencies
pip install -r requirements.txt
```

## Architecture

- **`_quarto.yml`** — master config: site title, navbar, footer, theme, analytics, grid layout
- **`styles.scss`** — all custom CSS/SCSS on top of the Darkly Bootstrap theme
- **`index.qmd`** — homepage / About page (uses Quarto `about: trestles` template)
- **`blog/blog_index.qmd`** — blog listing page
- **`blog/<category>/<post>.qmd`** — individual blog posts; each directory is a category
- **`files/`** — static assets served as-is (CV PDF, etc.) — listed as a resource in `_quarto.yml`
- **`_site/`** — generated output, never edit directly
- **`_freeze/`** — cached execution results; committed so CI doesn't re-run expensive notebooks

## Deployment

Two GitHub Actions workflows:
- **`deploy.yml`** — runs on push to `main`; renders and deploys `_site/` to the `gh-pages` branch
- **`build_preview.yml`** — runs on PRs; renders to `preview/pr-<N>/` on `gh-pages` for review before merging

The CI uses the latest Quarto pre-release. Keep local Quarto version in sync to avoid render discrepancies.

## Styling Notes

- Theme: `[darkly, styles.scss]` — Darkly Bootstrap base with overrides in `styles.scss`
- Color palette: background `#222`, text `#FDF6F6`, links `#2C9AB7`
- Custom utility classes in `styles.scss`: `.banner-image`, `.notice`, `.team-container`, `.highlight1`, `.centered`
- `execute: freeze: auto` in `_quarto.yml` means Python cells only re-execute when the source changes
