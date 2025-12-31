#!/usr/bin/env bash
# pr.sh - Git/PR automation for nfrax SDK repos
# Usage: ./scripts/pr.sh "commit message" "sync" "new" "branch" "force" "draft" "base"
#
# Arguments (passed from Makefile):
#   $1 - Commit message (required)
#   $2 - sync flag (0 or 1)
#   $3 - new flag (0 or 1)
#   $4 - explicit branch name (optional)
#   $5 - FORCE flag (0 or 1)
#   $6 - draft flag (0 or 1) - create PR as draft
#   $7 - base branch (optional) - target branch instead of default

set -euo pipefail

# --- Arguments ---
MSG="${1:-}"
SYNC_FLAG="${2:-0}"
NEW_FLAG="${3:-0}"
EXPLICIT_BRANCH="${4:-}"
FORCE_FLAG="${5:-0}"
DRAFT_FLAG="${6:-0}"
BASE_BRANCH="${7:-}"

# --- Validation ---
if [ -z "$MSG" ]; then
    echo "[pr] ERROR: Commit message cannot be empty."
    exit 1
fi

# --- Conventional Commits Check ---
if ! echo "$MSG" | grep -qE "^(feat|fix|docs|chore|refactor|perf|test|ci|build)(\([^)]+\))?!?: .+"; then
    if [ "$FORCE_FLAG" != "1" ]; then
        echo "[pr] ERROR: Commit message must follow Conventional Commits format."
        echo "    Expected: type(scope)?: description"
        echo "    Types: feat|fix|docs|chore|refactor|perf|test|ci|build"
        echo "    Example: feat: add new feature"
        echo "    Override with: make pr m=\"...\" FORCE=1"
        exit 1
    else
        echo "[pr] WARNING: Non-conventional commit (FORCE=1 override)"
    fi
fi

# --- Prerequisites ---
gh auth status >/dev/null 2>&1 || { echo "[pr] ERROR: gh CLI not authenticated. Run 'gh auth login' first."; exit 1; }
git remote get-url origin >/dev/null 2>&1 || { echo "[pr] ERROR: remote 'origin' not found."; exit 1; }

# --- Check for in-progress rebase/merge ---
if [ -d .git/rebase-apply ] || [ -d .git/rebase-merge ] || [ -f .git/MERGE_HEAD ]; then
    echo "[pr] ERROR: Rebase or merge in progress. Resolve it first."
    echo "    To abort: git rebase --abort  OR  git merge --abort"
    exit 1
fi

# --- Branch Detection ---
REPO_DEFAULT_BRANCH=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || echo main)
CURRENT_BRANCH=$(git branch --show-current || true)
if [ -z "$CURRENT_BRANCH" ]; then
    echo "[pr] ERROR: Detached HEAD state. Checkout a branch first."
    exit 1
fi

# --- Normalize Flags ---
if [ "$SYNC_FLAG" != "1" ]; then SYNC_FLAG="0"; fi
if [ "$NEW_FLAG" != "1" ]; then NEW_FLAG="0"; fi
if [ "$DRAFT_FLAG" != "1" ]; then DRAFT_FLAG="0"; fi

# --- Determine effective base branch ---
# BASE_BRANCH is the target for the PR (can be overridden)
# REPO_DEFAULT_BRANCH is used to decide "am I on the default branch?" flow
if [ -n "$BASE_BRANCH" ]; then
    # Validate that the base branch exists on remote
    if ! git ls-remote --exit-code --heads origin "$BASE_BRANCH" >/dev/null 2>&1; then
        echo "[pr] ERROR: Base branch '$BASE_BRANCH' does not exist on remote."
        exit 1
    fi
    echo "[pr] Using custom base branch: $BASE_BRANCH"
else
    BASE_BRANCH="$REPO_DEFAULT_BRANCH"
fi

# --- Python Detection (for random string generation) ---
PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    if command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        echo "[pr] ERROR: python3 or python not found in PATH."
        exit 1
    fi
fi

# --- Helper: Generate Branch Name ---
generate_branch_name() {
    local msg="$1"
    local timestamp=$(date -u +%m%d%H%M%S)
    local rand=$($PYTHON_CMD -c "import secrets,string; print(''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(4)))")
    local msg_no_prefix=$(echo "$msg" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[ ]*//')
    local slug=$(echo "$msg_no_prefix" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-40)
    [ -z "$slug" ] && slug="change"
    echo "${slug}-${timestamp}-${rand}"
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

if [ "$CURRENT_BRANCH" = "$REPO_DEFAULT_BRANCH" ] || [ "$NEW_FLAG" = "1" ]; then
    # --- Creating New PR (from repo default branch or with new=1) ---

    # Fetch to get accurate base comparison
    git fetch origin "$BASE_BRANCH" >/dev/null

    # Determine if working tree is dirty and count commits ahead of base
    DIRTY=0
    [ -n "$(git status --porcelain)" ] && DIRTY=1

    PR_COMMITS=$(git rev-list --count "origin/$BASE_BRANCH"..HEAD 2>/dev/null || echo 0)

    # On repo default branch: require dirty working tree
    if [ "$CURRENT_BRANCH" = "$REPO_DEFAULT_BRANCH" ] && [ "$DIRTY" = "0" ]; then
        echo "[pr] Nothing to do: no changes detected on $REPO_DEFAULT_BRANCH."
        exit 0
    fi

    # new=1 on feature branch: allow clean tree if there are commits ahead
    if [ "$NEW_FLAG" = "1" ] && [ "$DIRTY" = "0" ] && [ "$PR_COMMITS" -eq 0 ]; then
        echo "[pr] Nothing to do: no commits ahead of origin/$BASE_BRANCH (PR would be empty)."
        exit 0
    fi

    if [ "$CURRENT_BRANCH" = "$REPO_DEFAULT_BRANCH" ]; then
        echo "[pr] On $REPO_DEFAULT_BRANCH - creating new PR for: $MSG"
    else
        echo "[pr] new=1 specified - creating new PR from $CURRENT_BRANCH for: $MSG"
        if [ "$PR_COMMITS" -gt 0 ]; then
            echo "[pr] This PR will include $PR_COMMITS commit(s) ahead of origin/$BASE_BRANCH."
        fi
    fi

    # Determine branch name
    if [ -n "$EXPLICIT_BRANCH" ]; then
        BRANCH="$EXPLICIT_BRANCH"
        # Validate branch name format
        if ! git check-ref-format --branch "$BRANCH" >/dev/null 2>&1; then
            echo "[pr] ERROR: Invalid branch name: $BRANCH"
            echo "    Branch names cannot contain spaces, ~, ^, :, ?, *, [, or \\"
            exit 1
        fi
        if git show-ref --verify --quiet "refs/heads/$BRANCH" 2>/dev/null; then
            echo "[pr] ERROR: Branch '$BRANCH' already exists locally."
            echo "    Use a different name or delete the existing branch."
            exit 1
        fi
        if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
            echo "[pr] ERROR: Branch '$BRANCH' already exists on remote."
            echo "    Use a different name, or checkout the existing branch:"
            echo "    git fetch origin && git checkout $BRANCH"
            exit 1
        fi
    else
        BRANCH=$(generate_branch_name "$MSG")
    fi

    # Fast-forward if on repo default branch
    if [ "$CURRENT_BRANCH" = "$REPO_DEFAULT_BRANCH" ]; then
        LOCAL_AHEAD=$(git rev-list --count "origin/$REPO_DEFAULT_BRANCH"..$REPO_DEFAULT_BRANCH 2>/dev/null || echo 0)
        if [ "$LOCAL_AHEAD" -gt 0 ]; then
            echo "[pr] ERROR: $REPO_DEFAULT_BRANCH has $LOCAL_AHEAD local commit(s) not on origin/$REPO_DEFAULT_BRANCH."
            echo "    Refusing to proceed. These commits would be lost:"
            echo ""
            git log --oneline "origin/$REPO_DEFAULT_BRANCH"..$REPO_DEFAULT_BRANCH | head -10
            echo ""
            echo "    Options:"
            echo "    • Push them: git push origin $REPO_DEFAULT_BRANCH"
            echo "    • Discard them: git reset --hard origin/$REPO_DEFAULT_BRANCH"
            exit 1
        fi
        git merge --ff-only "origin/$REPO_DEFAULT_BRANCH" 2>/dev/null || {
            echo "[pr] ERROR: $REPO_DEFAULT_BRANCH has diverged from origin (unexpected)."
            echo "    git fetch origin && git reset --hard origin/$REPO_DEFAULT_BRANCH"
            exit 1
        }
    fi

    # Show pending changes (before staging)
    if [ "$DIRTY" = "1" ]; then
        echo "[pr] Pending changes:"
        git status --short | head -20
        FILE_COUNT=$(git status --porcelain | wc -l | tr -d ' ')
        if [ "$FILE_COUNT" -gt 20 ]; then
            echo "    ... and $((FILE_COUNT - 20)) more files"
        fi
        echo ""
    fi

    # Create branch
    git checkout -b "$BRANCH"

    # Stage and commit only if dirty
    if [ "$DIRTY" = "1" ]; then
        git add -A

        # Show authoritative staged files
        echo "[pr] Files to be committed:"
        git diff --cached --name-status | head -20
        STAGED_COUNT=$(git diff --cached --name-only | wc -l | tr -d ' ')
        if [ "$STAGED_COUNT" -gt 20 ]; then
            echo "    ... and $((STAGED_COUNT - 20)) more files"
        fi
        echo ""

        if git diff --cached --quiet; then
            echo "[pr] ERROR: Nothing to commit after staging."
            echo "    Returning to previous branch."
            git checkout - >/dev/null 2>&1
            git branch -D "$BRANCH" 2>/dev/null || true
            exit 1
        fi

        git commit -m "$MSG"
    else
        # new=1 with clean tree: no commit needed, just creating branch from HEAD
        echo "[pr] Creating PR from existing commits (no new changes to commit)"
    fi

    git push --set-upstream origin "$BRANCH"

    # Create or detect existing PR
    if gh pr view --head "$BRANCH" >/dev/null 2>&1; then
        echo "[pr] PR already exists."
    else
        PR_CREATE_ARGS=(--title "$MSG" --body "$MSG" --base "$BASE_BRANCH" --head "$BRANCH")
        if [ "$DRAFT_FLAG" = "1" ]; then
            PR_CREATE_ARGS+=(--draft)
            echo "[pr] Creating as draft PR"
        fi
        gh pr create "${PR_CREATE_ARGS[@]}"
    fi

    echo ""
    echo "[pr] [OK] PR created: $(gh pr view --head "$BRANCH" --json url -q .url 2>/dev/null || true)"
    echo "[pr] You are now on branch: $BRANCH"
    echo ""
    echo "[pr] Next steps:"
    echo "    • Add more commits: make pr m=\"fix: another change\""
    echo "    • Return to $REPO_DEFAULT_BRANCH: git checkout $REPO_DEFAULT_BRANCH"
    echo ""
    echo "[pr] [!]  If creating another PR immediately, wait for this one to merge"
    echo "    or the new PR may conflict with this one."

else
    # --- Updating Existing PR (on feature branch) ---

    echo "[pr] On branch $CURRENT_BRANCH - updating/creating PR"

    # Check PR state
    PR_STATE=$(gh pr view --head "$CURRENT_BRANCH" --json state -q .state 2>/dev/null || echo "NONE")
    if [ "$PR_STATE" = "MERGED" ]; then
        echo "[pr] ERROR: PR for branch '$CURRENT_BRANCH' was already MERGED."
        echo "    Your commits won't reach $BASE_BRANCH by pushing to this branch."
        echo ""
        echo "    Options:"
        echo "    1. Create a new branch from current work:"
        echo "       make pr m=\"$MSG\" new=1"
        echo ""
        echo "    2. Switch to $REPO_DEFAULT_BRANCH and create a new PR:"
        echo "       git checkout $REPO_DEFAULT_BRANCH && make pr m=\"$MSG\""
        exit 1
    fi
    if [ "$PR_STATE" = "CLOSED" ]; then
        echo "[pr] WARNING: PR for branch '$CURRENT_BRANCH' was CLOSED (not merged)."
        echo "    Will create a new PR after pushing."
    fi

    # Check if behind
    git fetch origin "$BASE_BRANCH" >/dev/null
    BEHIND=$(git rev-list --count HEAD..origin/"$BASE_BRANCH" 2>/dev/null || echo 0)
    if [ "$BEHIND" -gt 0 ] && [ "$SYNC_FLAG" != "1" ]; then
        echo "[pr] WARNING: Branch is $BEHIND commits behind origin/$BASE_BRANCH."
        echo "    Consider: make pr m=\"...\" sync=1"
    fi

    # Rebase if sync=1
    if [ "$SYNC_FLAG" = "1" ]; then
        if [ -n "$(git status --porcelain)" ]; then
            echo "[pr] ERROR: sync=1 requires a clean working tree."
            echo "    Commit or stash your changes first, then run: make pr m=\"...\" sync=1"
            exit 1
        fi
        echo "[pr] Sync enabled - rebasing $CURRENT_BRANCH on origin/$BASE_BRANCH"
        git fetch origin "$CURRENT_BRANCH" >/dev/null 2>&1 || true
        if git rev-parse --verify origin/"$CURRENT_BRANCH" >/dev/null 2>&1; then
            if ! git merge-base --is-ancestor origin/"$CURRENT_BRANCH" HEAD; then
                echo "[pr] ERROR: Remote branch has commits not in your local branch."
                echo "    Refusing to rebase/force-push. Pull and reconcile first:"
                echo "    git pull origin $CURRENT_BRANCH"
                exit 1
            fi
        fi
        git rebase origin/"$BASE_BRANCH" || { echo "[pr] ERROR: Rebase failed. Run 'git rebase --abort' and resolve manually."; exit 1; }
    fi

    # Stage changes
    git add -A
    HAS_STAGED=0
    if ! git diff --cached --quiet; then
        HAS_STAGED=1
    fi

    # Check commits ahead
    AHEAD=0
    if git rev-parse --verify origin/"$CURRENT_BRANCH" >/dev/null 2>&1; then
        AHEAD=$(git rev-list --count origin/"$CURRENT_BRANCH"..HEAD 2>/dev/null || echo 0)
    else
        AHEAD=1
    fi

    # Early exit if nothing to do
    if [ "$HAS_STAGED" = "0" ] && [ "$AHEAD" = "0" ] && [ "$SYNC_FLAG" != "1" ]; then
        echo "[pr] Nothing to do: no staged changes and no commits to push."
        echo "    Make some changes first, then run: make pr m=\"...\""
        exit 0
    fi

    # Commit if there are staged changes
    if [ "$HAS_STAGED" = "1" ]; then
        echo "[pr] Files to be committed:"
        git diff --cached --name-status | head -20
        STAGED_COUNT=$(git diff --cached --name-only | wc -l | tr -d ' ')
        if [ "$STAGED_COUNT" -gt 20 ]; then
            echo "    ... and $((STAGED_COUNT - 20)) more files"
        fi
        echo ""
        git commit -m "$MSG"
        if git rev-parse --verify origin/"$CURRENT_BRANCH" >/dev/null 2>&1; then
            AHEAD=$(git rev-list --count origin/"$CURRENT_BRANCH"..HEAD 2>/dev/null || echo 0)
        else
            AHEAD=1
        fi
    else
        echo "[pr] No staged changes to commit"
    fi

    # Push
    if [ "$SYNC_FLAG" = "1" ]; then
        git push --force-with-lease origin "$CURRENT_BRANCH"
    elif [ "$AHEAD" -gt 0 ]; then
        git push -u origin "$CURRENT_BRANCH"
    else
        echo "[pr] No commits to push"
    fi

    # Create or update PR
    if gh pr view --head "$CURRENT_BRANCH" >/dev/null 2>&1; then
        echo ""
        echo "[pr] [OK] PR updated: $(gh pr view --head "$CURRENT_BRANCH" --json url -q .url)"
    else
        PR_CREATE_ARGS=(--title "$MSG" --body "$MSG" --base "$BASE_BRANCH" --head "$CURRENT_BRANCH")
        if [ "$DRAFT_FLAG" = "1" ]; then
            PR_CREATE_ARGS+=(--draft)
            echo "[pr] Creating as draft PR"
        fi
        gh pr create "${PR_CREATE_ARGS[@]}"
        echo ""
        echo "[pr] [OK] PR created: $(gh pr view --head "$CURRENT_BRANCH" --json url -q .url 2>/dev/null || true)"
    fi
    echo "[pr] You are on branch: $CURRENT_BRANCH"
fi
