# Hephaestus Project Guidelines

This file helps Claude understand the project conventions for contributing to Hephaestus.

## Project Context
- **Repository**: Hephaestus - Semi-Structured Agentic Framework
- **Maintainer**: Ido-Levi (original author)
- **Fork**: mikez93/Hephaestus
- **Working Branch**: local/customizations (personal work)
- **PR Branches**: pr/* (clean branches for pull requests)

## Pull Request Guidelines

When creating PRs for this project, follow these conventions:

### Documentation Location
- ✅ All documentation goes in `website/docs/`
- ✅ Getting started guides go in `website/docs/getting-started/`
- ✅ Update `website/sidebars.ts` when adding new docs
- ❌ Never put docs in `Mike/docs/` or `docs/` directories

### Configuration Files
- ✅ Use generic paths like `./your_project` in `hephaestus_config.yaml`
- ❌ Never commit personal paths like `/Users/mike/...`
- ✅ Keep personal configs in `*.local.yaml` (gitignored)

### Code Style
- Follow existing patterns in the codebase
- Use descriptive commit messages (conventional commits format)
- Keep changes focused and atomic
- Test changes before submitting PR

### Common Cleanup Tasks for PRs
Before creating a PR, ensure:
1. No personal paths in config files
2. No `Mike/docs/` or `docs/LOCAL_SETUP.md` files
3. All docs in correct `website/docs/` location
4. No typos in config (e.g., "Configurationr" → "Configuration")
5. Update `website/sidebars.ts` if adding docs
6. No database files or API keys

## Branch Strategy
- `main`: Tracks upstream, never work here directly
- `local/customizations`: Personal work, may have local paths/configs
- `pr/*`: Clean branches for PRs, created from upstream/main

## Custom Commands Available

Use these slash commands for efficient PR workflow:

### `/pr-prep <branch-name>`
Creates a clean PR branch from upstream with auto-cleanup
- Fetches latest upstream
- Cherry-picks your commits
- Removes personal paths
- Ensures docs in correct location

### `/pr-create`
Pushes branch and creates PR to Ido's repository
- Must be run from a `pr/*` branch
- Auto-generates PR description
- Returns PR URL

### `/sync-upstream`
Updates your work with latest upstream changes
- Rebases local/customizations
- Handles conflicts
- Keeps you in sync

## Maintainer Preferences (Ido)
- Prefers docs in `website/docs/` for documentation site
- Appreciates atomic, well-tested commits
- Responds quickly to clean, focused PRs
- Values clear commit messages and PR descriptions

## Testing
Before submitting PR:
- Ensure system starts without errors
- Test the specific feature you changed
- Check logs for unexpected warnings
- Verify configuration loads correctly

## Git Remotes
- `upstream`: https://github.com/Ido-Levi/Hephaestus.git (Ido's repo)
- `origin` or `fork`: https://github.com/mikez93/Hephaestus.git (your fork)
