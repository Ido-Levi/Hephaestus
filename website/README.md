# Hephaestus Documentation Website

This directory contains the Docusaurus-powered documentation website for Hephaestus.

Built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

## Quick Start

### Development

Run the development server:

```bash
cd website
npm install  # First time only
npm start
```

The site will be available at `http://localhost:3000/Hephaestus/`

If port 3000 is already in use, you can specify a different port:

```bash
npm start -- --port 3001
```

Most changes are reflected live without having to restart the server.

### Build

Build the static website:

```bash
npm run build
```

The built site will be in the `build/` directory.

### Local Preview

Preview the built site locally:

```bash
npm run serve
```

## Deployment to GitHub Pages

### Prerequisites

1. Update `docusaurus.config.ts` with your GitHub username:
   - Change `url` to your GitHub Pages URL: `https://your-username.github.io`
   - Change `organizationName` to your GitHub username
   - Set `baseUrl` to `/Hephaestus/` (or your repo name)

2. Add a `.nojekyll` file to `static/` directory (already included)

### Manual Deployment

Deploy using the built-in deploy command:

```bash
GIT_USER=your-username npm run deploy
```

Or using SSH:

```bash
USE_SSH=true npm run deploy
```

This will:
1. Build the site
2. Push to the `gh-pages` branch
3. GitHub Pages will automatically serve it

### Automated Deployment with GitHub Actions

Create `.github/workflows/deploy-docs.yml` in your repository root:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'website/**'
      - 'docs/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: cd website && npm install

      - name: Build website
        run: cd website && npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./website/build
```

Then enable GitHub Pages:
1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `root`
4. Save

## Documentation Structure

```
website/
├── docs/               # Documentation content (markdown files)
│   ├── intro.md       # Homepage/welcome page
│   ├── core/          # Core systems documentation
│   ├── features/      # Features documentation
│   ├── sdk/           # SDK guides
│   ├── workflows/     # Workflow guides
│   └── design/        # Design documents
├── src/
│   ├── components/    # React components
│   └── pages/         # Custom pages (landing page)
├── static/            # Static assets (images, etc.)
├── docusaurus.config.ts  # Main configuration
└── sidebars.ts        # Sidebar navigation structure
```

## Adding Documentation

### Create a New Doc

1. Create a markdown file in the appropriate `docs/` subdirectory
2. Add front matter at the top:

```markdown
---
sidebar_position: 1
title: Your Page Title
---

# Your Page Title

Content here...
```

3. The sidebar will automatically include it based on the configuration in `sidebars.ts`

### Update Sidebar

Edit `sidebars.ts` to control sidebar navigation:

```typescript
{
  type: 'category',
  label: 'Your Category',
  items: ['path/to/doc1', 'path/to/doc2'],
}
```

## Troubleshooting

### Compilation Errors

If you encounter MDX compilation errors about unexpected characters:
- Check for `<` or `>` characters in markdown that might be interpreted as JSX
- Escape them using HTML entities: `&lt;` and `&gt;`
- Or use inline code: `` `<0.2` ``

### Broken Links

The build will warn about broken internal links. Fix them by:
- Using relative paths: `../other-doc.md`
- Or Docusaurus-style paths: `other-doc` (without `.md`)

### Port Already in Use

If port 3000 is taken, use a different port:

```bash
npm start -- --port 3001
```

## Features

- ✅ All existing documentation migrated
- ✅ Custom homepage with Hephaestus branding
- ✅ Organized sidebar with emojis
- ✅ Search functionality (built-in)
- ✅ Dark mode support
- ✅ Mobile responsive
- ✅ Fast performance
- ✅ SEO optimized

## Configuration

Main configuration file: `docusaurus.config.ts`

Key settings:
- `title`: Site title
- `tagline`: Site tagline
- `url`: Production URL
- `baseUrl`: Base path for the site
- `organizationName`: GitHub org/username
- `projectName`: GitHub repo name

## Resources

- [Docusaurus Documentation](https://docusaurus.io/docs)
- [Deployment Guide](https://docusaurus.io/docs/deployment)
- [MDX Guide](https://docusaurus.io/docs/markdown-features)
