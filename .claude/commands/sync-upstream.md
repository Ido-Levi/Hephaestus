# Sync with Upstream

Update local/customizations branch with latest changes from Ido's upstream repository.

**Use this weekly or when Ido merges changes to keep your work up to date.**

## Steps to Execute:

1. **Fetch latest from all remotes**
   - Run `git fetch upstream`
   - Run `git fetch origin`
   - Show what's new in upstream/main

2. **Update main branch**
   - Checkout `main` branch
   - Reset to `upstream/main` (hard reset)
   - Push to `origin main --force` (update your fork)

3. **Rebase local/customizations**
   - Checkout `local/customizations` branch
   - Show current status with `git status`
   - Rebase onto `upstream/main`

4. **Handle conflicts if they occur**
   - If conflicts, pause and show the conflicting files
   - Provide guidance on resolution:
     - Keep your local config changes
     - Accept upstream changes for code
     - Review each conflict carefully
   - After resolution, guide me through `git rebase --continue`

5. **Verify sync completed**
   - Show final status
   - Show how many commits ahead of upstream
   - Confirm everything merged cleanly

6. **Optional: Update origin**
   - Ask if I want to push updated `local/customizations` to origin
   - If yes: `git push origin local/customizations --force-with-lease`

## Success Criteria:
- ✅ main branch updated to upstream/main
- ✅ local/customizations rebased on latest upstream
- ✅ No conflicts or conflicts resolved
- ✅ Your work preserved and up to date

## If Conflicts Occur:
Don't panic! Guide me through resolution:
1. Show which files conflict
2. For each file, explain the conflict
3. Suggest whether to keep ours, theirs, or manual merge
4. After resolution, continue rebase

## Warning:
This operation force-updates branches. Make sure:
- You've committed any work in progress
- You're okay with rewriting history on local/customizations
- You have a backup of important work
