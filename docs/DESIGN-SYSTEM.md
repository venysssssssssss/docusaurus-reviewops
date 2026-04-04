# Design System

Visual identity, component patterns, and CSS architecture for the Engineering Docs portal.

## Color Palette

### Primary Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `--ifm-color-primary` | `#2e86ab` | `#47aad2` | Links, buttons, accents |
| `--ifm-color-primary-dark` | `#287697` | `#31a0cc` | Hover states |
| `--ifm-color-primary-darker` | `#25708e` | `#2b9ac5` | Active states |
| `--ifm-color-primary-darkest` | `#1e5c76` | `#2381a3` | Strong emphasis |
| `--ifm-color-primary-light` | `#3496bf` | `#5db4d8` | Subtle backgrounds |
| `--ifm-color-primary-lighter` | `#379cc8` | `#69b9db` | Borders |
| `--ifm-color-primary-lightest` | `#47aad2` | `#8bcae3` | Badges, pills |

### Semantic Colors

Inherited from Docusaurus theme:
- **Success**: Green — used in :::tip admonitions
- **Warning**: Orange — used in :::warning admonitions
- **Danger**: Red — used in :::danger admonitions
- **Info**: Blue — used in :::info admonitions

## Typography

| Property | Value | Rationale |
|----------|-------|-----------|
| Line height | 1.75 | Improved readability for technical docs |
| Paragraph spacing | 1.25rem | Clear separation between blocks |
| Heading spacing | 0.75rem | Tight coupling with content below |
| Code font size | 95% | Slightly smaller than body text |
| Global radius | 0.5rem | Consistent rounded corners |

## Component Patterns

### Navbar (Frosted Glass)

Inspired by Vercel Docs. Semi-transparent background with backdrop blur:

```css
.navbar {
  backdrop-filter: blur(8px);
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 1px 0 0 rgba(0, 0, 0, 0.08);
}
```

Dark mode adjusts background to `rgba(30, 30, 30, 0.85)`.

### Sidebar Active Link (Accent Border)

Inspired by Stripe Docs. Active item gets a colored left border:

```css
.menu__link--active:not(.menu__link--sublist) {
  border-left: 3px solid var(--ifm-color-primary);
  background: rgba(46, 134, 171, 0.08);
  border-radius: 0 0.5rem 0.5rem 0;
}
```

### Cards (Category Index)

Inspired by Tailwind Docs. Hover lifts the card:

```css
.card {
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}
```

### Hero Section (Homepage)

Gradient banner on the homepage:

```css
.hero-section {
  background: linear-gradient(135deg, #2e86ab 0%, #1e5c76 100%);
  color: white;
  padding: 2.5rem 2rem;
  border-radius: 1rem;
}
```

Used as a wrapper div in `docs/index.md`.

### Admonitions

Standard Docusaurus admonitions with enhanced styling:

```css
.admonition {
  border-radius: 0.5rem;
  border-left-width: 4px;
}
```

Usage in markdown:

```markdown
:::tip Title
Content here.
:::

:::warning Title
Content here.
:::

:::danger Title
Content here.
:::

:::info Title
Content here.
:::
```

### Code Blocks

Rounded corners and styled title bar:

```css
.prism-code { border-radius: 0.5rem; }
div[class*="codeBlockTitle"] {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 0.85rem;
  letter-spacing: 0.02em;
}
```

Usage in markdown:

````markdown
```bash title="Install dependencies"
make setup
```
````

### Tables (Responsive)

Tables scroll horizontally on mobile:

```css
.markdown table {
  display: block;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

### Footer

Inspired by GitHub Docs. Clean separator and uppercase titles:

```css
.footer {
  border-top: 1px solid var(--ifm-toc-border-color);
}
.footer__title {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
}
```

## Static Assets

| Asset | Path | Format | Purpose |
|-------|------|--------|---------|
| Favicon | `static/img/favicon.svg` | SVG | Brand initials "ED" on #2e86ab |
| Social Card | `static/img/social-card.png` | PNG 1200x630 | OG/Twitter cards |
| robots.txt | `static/robots.txt` | Text | SEO crawl directives |

### Favicon Design

SVG with rounded rect background and white text:

```svg
<svg viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#2e86ab"/>
  <text x="32" y="42" font-size="28" font-weight="700"
        fill="#fff" text-anchor="middle">ED</text>
</svg>
```

## Search

Local offline search powered by `@easyops-cn/docusaurus-search-local` (lunr.js):

- **Keyboard shortcut**: Ctrl+K / Cmd+K
- **Languages indexed**: Portuguese, English
- **Blog indexing**: Disabled
- **No external service required** (no Algolia account needed)

## Diagrams

Mermaid diagrams render natively via `@docusaurus/theme-mermaid`:

- Auto-themed for light/dark mode
- Diff-able in PRs (text-based, not images)
- Supported types: flowchart, sequence, graph, gantt, etc.

```markdown
```mermaid
graph LR
    A --> B --> C
```​
```

## Dark Mode

- `respectPrefersColorScheme: true` — auto-detects OS preference
- All custom CSS has `[data-theme="dark"]` variants
- Hero section gradient adjusts for dark backgrounds
- Card shadows increase opacity in dark mode

## Announcement Bar

Dismissible banner for important notices:

```typescript
announcementBar: {
  id: "setup-notice",
  content: "...",
  backgroundColor: "#2e86ab",
  textColor: "#fff",
  isCloseable: true,
}
```

Remove or update in `docusaurus.config.ts` after initial setup.

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `docs-site/src/css/custom.css` | ~200 | All visual customizations |
| `docs-site/docusaurus.config.ts` | ~160 | Theme config, plugins, colors |
| `docs-site/static/img/favicon.svg` | 4 | Brand favicon |
| `docs-site/static/img/social-card.png` | binary | Social sharing image |
| `docs-site/src/pages/404.tsx` | 16 | Custom 404 page |
