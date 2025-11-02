# Create Pull Request

Push the current branch to fork and create a pull request to Ido's repository.

**Prerequisites:** Must be on a `pr/*` branch (created by `/pr-prep`)

## Steps to Execute:

1. **Verify current branch**
   - Check we're on a `pr/*` branch
   - If not, stop and tell me to run `/pr-prep` first

2. **Show final changes**
   - Run `git diff upstream/main --stat`
   - Run `git log upstream/main..HEAD --oneline`
   - Summarize what will be in the PR

3. **Ask for confirmation**
   - "Ready to push and create PR? (y/n)"
   - Wait for my approval

4. **Push to fork**
   - Push current branch to `fork` remote (or `origin` if fork doesn't exist)
   - Use: `git push fork HEAD` or `git push origin HEAD`

5. **Create pull request**
   - Use `gh pr create` with:
     - `--repo Ido-Levi/Hephaestus`
     - `--base main`
     - `--head mikez93:CURRENT-BRANCH`
     - `--title` from latest commit message
     - `--body` with brief description and "See commit messages for details"

6. **Return PR URL**
   - Display the PR URL
   - Remind me to:
     - Add any additional context in PR description
     - Watch for Ido's feedback
     - Be ready to make quick fixes if needed

## Success Criteria:
- ✅ Branch pushed to fork
- ✅ PR created on Ido-Levi/Hephaestus
- ✅ PR URL provided
- ✅ Clean, professional presentation

## If PR Creation Fails:
- Check if `gh` CLI is authenticated
- Verify fork remote is configured
- Provide manual instructions to create PR via GitHub web UI
