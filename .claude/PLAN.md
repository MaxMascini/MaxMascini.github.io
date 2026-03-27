# MinMaxed v2 — Personal Website Rebuild Plan

## Context

The current site is built with Quarto (a scientific publishing framework) and hosted on GitHub Pages. While functional, Quarto is heavyweight for a personal site and limits creative control over the visual design. The goal is to replace it with a modern, hand-crafted site with a beautiful interactive landing page, a blog, and a portfolio section — while keeping the same GitHub Pages hosting at `https://maxmascini.github.io/`.

---

## Tech Stack: Astro

**Astro 4.x** is the right choice because:
- Ships zero JS by default → fast landing page
- First-class Markdown/MDX for the blog
- File-based routing (one `.astro` file = one page)
- GitHub Pages deployment is fully supported via official actions
- Existing `.qmd` blog posts migrate to `.md` with minimal changes
- Tailwind CSS integrates as a first-party plugin

Key packages: `@astrojs/tailwind`, `@astrojs/mdx`, `@astrojs/sitemap`, `@astrojs/rss`, `astro-icon`, `@tailwindcss/typography`

---

## Design Direction: "Topographic Intelligence"

Borrows from two of Max's worlds: topographic maps (outdoors) and neural network diagrams (neuroscience/AI). Clean, data-forward, dark, with warmth.

### Color Palette

| Role | Hex | Notes |
|---|---|---|
| Background | `#1a1a2e` | Slightly blue-shifted from current `#222` |
| Surface (cards) | `#16213e` | Elevated surfaces |
| Primary accent | `#2C9AB7` | Keep existing teal — it's the site identity |
| Teal light | `#4fc3f7` | Hover states |
| Sage green | `#4caf82` | Outdoors/nature context (trail posts, tags) |
| Amber | `#f6a623` | Sparingly for CTAs |
| Text | `#e8eaf0` | Main body |
| Muted text | `#8892a4` | Dates, metadata |

### Typography
- **Headings:** Inter Variable (clean, modern, technical)
- **Body/Blog prose:** Source Serif 4 Variable (makes long-form feel intentional)
- **Code:** JetBrains Mono

### Animation Philosophy
Restraint. Animations serve orientation, not decoration:
- Scroll reveal: sections fade + translate up via `IntersectionObserver` (~20 lines JS)
- Hero: animated SVG topographic contour lines (CSS `stroke-dashoffset` animation)
- Hover: card lift (`translateY(-4px)` + shadow) — CSS only
- Nav: sticky with `backdrop-filter: blur()` activating on scroll
- No scroll-jacking, no parallax, no page transitions

---

## Pages

```
/              → Landing page (hero + quick bio + featured projects + recent posts)
/about         → Full bio, timeline, interests, CV download
/blog          → Blog index with tag filter
/blog/[slug]   → Individual post (MDX capable)
/projects      → Portfolio grid with tag filter
/research      → Research focus, interests, publications (starts sparse)
/contact       → Email/social links, location
/404           → Custom 404
```

### Landing Page Sections
1. **Hero** — Full viewport, animated SVG topo background, name + typewriter subtitle ("CS Researcher" / "Backpacker" / "Neuroscience Alum"), two CTAs
2. **Quick Bio Strip** — Photo (teal ring), 3-sentence bio, quick stats, social links
3. **Featured Work** — 2–3 project cards flagged `featured: true`
4. **Recent Posts** — Latest 2 blog cards
5. **Research Teaser** — One-liner + link to `/research`
6. **Footer** — Nav | Social | Copyright

### About Page
- Full bio (longer than landing)
- **Timeline component**: neuroscience undergrad start → first-class honours + neurotechnology cert → ECT thru-hike → MCS start → SURGE role → present
- Interests cards: AI Research | Data Visualization | Backpacking
- CV download button (PDF)

### Blog
- Tag filter bar (client-side, ~30 lines JS, no library): All | Tutorial | Outdoors | Research
- Card grid: image, date, title, description, tags
- Post pages: reading time estimate, prev/next navigation, tag links

### Projects
- Project cards: title, description, tech stack badges, GitHub/live links
- Same tag filter pattern as blog
- Projects defined in `src/content/projects/` collection

### Research
- Current research area (human-AI interaction, theory of mind)
- Research interests list
- Publications section (placeholder initially, grows over time)
- Dalhousie affiliation, CV link

### Additional Suggestions
- **`/now` page** — A short "currently" update (what I'm working on, reading, last trail). Shows the site is alive. Easy to maintain.
- **Speaking/Writing** — Add to Research page initially, promote when content grows
- **Interactive data viz showcase** — Future: embed a D3/Observable trail elevation profile from the ECT using public DEM data. Strong differentiator given the data viz interest.
- **Utterances comments** — Already configured in Quarto; migrates easily as an Astro script component when ready.

---

## Folder Structure

```
MaxMascini.github.io/
├── .github/workflows/deploy.yml     ← Replace existing Quarto workflow
├── public/
│   ├── files/Academic_CV_Jan_2026.pdf
│   ├── images/{max_kitty_pic.jpg, max_surge_pic.jpg}
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── layout/{Header, Footer, SEOHead}.astro
│   │   ├── ui/{BlogCard, ProjectCard, TagBadge, TimelineItem, SocialLinks}.astro
│   │   └── home/{Hero, FeaturedProjects, RecentPosts, TopoBackground}.astro
│   ├── content/
│   │   ├── config.ts                ← Content collection schemas
│   │   ├── blog/
│   │   │   ├── quarto-website-tutorial.md   ← Migrated from .qmd
│   │   │   └── east-coast-trail.md          ← Migrated from .qmd
│   │   └── projects/
│   │       └── *.md
│   ├── layouts/{BaseLayout, BlogPostLayout, PageLayout}.astro
│   ├── pages/
│   │   ├── index.astro
│   │   ├── about.astro
│   │   ├── research.astro
│   │   ├── contact.astro
│   │   ├── blog/{index.astro, [...slug].astro}
│   │   ├── projects/index.astro
│   │   └── 404.astro
│   └── styles/global.css
├── astro.config.mjs
├── tailwind.config.mjs
├── package.json
└── tsconfig.json
```

---

## Blog Migration

Both existing posts migrate from `.qmd` to `.md`:

**East Coast Trail** (`blog/outdoors/east-coast-trail.qmd`) — Near-clean migration:
- Fix date format: `"24-11-2024"` → `2024-11-24`
- Add a `description` field
- Body prose is standard Markdown — preserves as-is

**Quarto Tutorial** (`blog/1.making-quarto-website/quarto-website-tut.qmd`) — Needs more cleanup:
- Remove Quarto-only YAML fields (`title-block-banner`, `execute`, `comments` utterances config)
- Replace `` `r Sys.Date()` `` with a literal date
- Replace `{.lightbox}` image syntax with standard `![alt](path)`

---

## GitHub Actions Deployment

Replace `.github/workflows/deploy.yml` entirely. New workflow uses the official GitHub Pages API (no `gh-pages` branch):

```yaml
name: Deploy Astro Site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with: { path: ./dist }

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

**One-time GitHub setting change required:** Repo Settings → Pages → Source: change from "Deploy from branch (gh-pages)" to "GitHub Actions".

Build time drops from ~3-4 minutes (Quarto + Python) to ~20-30 seconds.

---

## Google Analytics

Existing GTM container `GTM-TJ454JG2` moves to a `<script>` tag in `SEOHead.astro` (included in `BaseLayout.astro`). No GTM container changes needed. Cookie consent handled by a simple localStorage-based vanilla JS banner component.

---

## Implementation Order

1. **Foundation** — Init Astro (empty template), configure integrations, build Header/Footer/BaseLayout, set up Tailwind tokens
2. **Content Layer** — Define collection schemas, migrate both blog posts, build `[...slug].astro` + `BlogCard.astro` + `/blog/index.astro`
3. **Landing Page** — Hero with topo SVG animation, typewriter, bio strip, featured projects, recent posts sections, scroll-reveal
4. **Remaining Pages** — About (with timeline), Projects (with tag filter), Research, Contact, 404
5. **Polish & Deploy** — New `deploy.yml`, switch Pages source to Actions, SEO/OG tags, image optimization, mobile pass, first deploy

---

## Critical Files (Current Repo)

| File | Action |
|---|---|
| `.github/workflows/deploy.yml` | Replace entirely with Astro workflow above |
| `blog/outdoors/east-coast-trail.qmd` | Migrate to `src/content/blog/east-coast-trail.md` |
| `blog/1.making-quarto-website/quarto-website-tut.qmd` | Migrate with cleanup to `src/content/blog/quarto-website-tutorial.md` |
| `index.qmd` | Source for bio text and social links to port to landing + about pages |
| `styles.scss` | Reference for existing color values (`#2C9AB7`, `#222`) to carry forward |
| `files/Academic_CV_Jan_2026.pdf` | Move to `public/files/` |
| `images/` | Move all to `public/images/` |

---

## Verification Checklist

- [ ] `npm run dev` locally: all pages render, blog posts display correctly, tag filters work
- [ ] `npm run build` passes with no errors
- [ ] Push to main: GitHub Actions deploy succeeds, site live at `https://maxmascini.github.io/`
- [ ] Sitemap at `/sitemap-index.xml`, RSS at `/rss.xml`
- [ ] 404 page works, CV PDF downloads correctly
- [ ] Mobile: test hero, blog cards, and project grid on 375px viewport
