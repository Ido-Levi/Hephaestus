# Prepare Clean PR Branch

Create a new PR branch from upstream/main with clean code for submission to Ido's repository.

**Arguments:** Branch name (e.g., `/pr-prep fix-monitoring`)

## Steps to Execute:

1. **Fetch latest from upstream**
   - Run `git fetch upstream`
   - Run `git fetch origin`

2. **Create new branch**
   - Create branch `pr/$ARGUMENTS` from `upstream/main`
   - Switch to the new branch

3. **Cherry-pick commits**
   - Ask me which commits from `local/customizations` to include
   - Show recent commits with `git log --oneline local/customizations -10`
   - Cherry-pick the specified commits

4. **Clean the branch for PR**
   - Delete entire `Mike/` directory (personal workspace)
   - Delete `docs/LOCAL_SETUP.md` if it exists
   - Replace any `/Users/mike/*` paths with `./your_project` in `hephaestus_config.yaml`
   - Verify all docs are in `website/docs/` (not in Mike/ or docs/)
   - Check for typos like "Configurationr" and fix them
   - Ensure no personal database paths, API keys, or *.local.yaml files

5. **Show the result**
   - Run `git status`
   - Run `git diff upstream/main --stat`
   - Show summary of what will be in the PR

6. **Wait for confirmation**
   - Ask if the changes look good
   - Suggest any additional cleanup if needed

## Success Criteria:
- ✅ Branch created from latest upstream/main
- ✅ Only relevant commits included
- ✅ No personal paths (all use `./your_project`)
- ✅ All docs in `website/docs/`
- ✅ Ready for PR creation

**Next step:** Run `/pr-create` to push and create the pull request.
