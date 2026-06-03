# Git Recovery for jira-evm-visualizer

You are seeing this because your local directory has untracked files that match the remote repository's `main` branch. This happened because the project files were initially created directly (not via `git clone`).

The remote is at: https://github.com/eklarson/jira-evm-visualizer

## Safe Recovery Steps (Recommended)

Run these commands from inside `~/Projects/jira-evm-visualizer`:

```bash
# 1. Make sure .gitignore is present (we added it if missing)
# (If you see this file, it's already handled)

# 2. Stage all the current files (including the new .gitignore)
git add .

# 3. Commit them as your initial local state
git commit -m "Initial local project files from setup"

# 4. Rename local branch to main if not already
git branch -M main

# 5. Set up tracking with remote main
git branch --set-upstream-to=origin/main main

# 6. Pull any updates from remote (allow unrelated histories because local had no prior commits)
git pull origin main --allow-unrelated-histories
```

After this, you should be on `main`, tracking `origin/main`, and `git status` will be clean (or show only your local changes).

## Alternative: Let Checkout Overwrite (if you want remote version exactly)

**WARNING**: This will replace your local untracked files with the versions from the remote. Only do this if you are sure your local files are identical or you don't care about differences.

```bash
# First, move the conflicting files aside (or delete if you trust remote)
mkdir -p ../backup-jira-evm-files
mv .dockerignore .env.example Dockerfile GRAFANA_SETUP.md README.md app/ monitoring/ requirements.txt scripts/ tests/ ../backup-jira-evm-files/ 2>/dev/null || true

# Now checkout
git checkout -b main --track origin/main

# Then restore your local files if needed, or just use the cloned ones
# cp -r ../backup-jira-evm-files/* ./
```

## After Recovery

```bash
git status
git log --oneline -5
git remote -v
```

You can now push/pull normally.

If you had a `.venv` or other ignored files, they should stay because of `.gitignore`.

## Why this error occurred

- `git init` + `git remote add` + `git fetch` creates a situation where the working tree has "untracked" files.
- `git checkout -b main --track origin/main` tries to materialize the branch's tree into the working directory.
- Git refuses to overwrite untracked files to protect your work.

Committing first (as in the recommended steps) is the safest way to "claim" the files under git control.

## Next Steps

- Once recovered, you can `git push -u origin main` if you want to push your local commit.
- Continue development.
- For the Docker/Grafana setup, see the main README and GRAFANA_SETUP.md.

If you run into merge conflicts or other errors during the above, paste the output here for further help.