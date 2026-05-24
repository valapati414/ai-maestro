#!/usr/bin/env bash
#
# GitHub Environment Info Collector for ai-maestro
# Run: bash setup-github-info.sh
#
# This script gathers GitHub, git, and environment details
# needed to start working on your forked repository.
# It does NOT collect any secrets, tokens, or API keys.
#

set -euo pipefail

REPO="valapati414/ai-maestro"
SEPARATOR="================================================================"
THINSEP="----------------------------------------------------------------"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; }
info() { echo -e "  ${CYAN}[INFO]${NC} $1"; }
heading() { echo -e "\n${BOLD}$1${NC}"; echo "$SEPARATOR"; }

echo ""
echo "  ██████╗ ██╗███████╗████████╗ █████╗ ██████╗ ████████╗"
echo "  ██╔══██╗██║██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝"
echo "  ██████╔╝██║███████╗   ██║   ███████║██████╔╝   ██║   "
echo "  ██╔═══╝ ██║╚════██║   ██║   ██╔══██║██╔══██╗   ██║   "
echo "  ██║     ██║███████║   ██║   ██║  ██║██║  ██║   ██║   "
echo "  ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
echo ""
echo "  GitHub Environment Collector"
echo "  Repo: https://github.com/$REPO"
echo "$SEPARATOR"

# Store all output for final summary
OUTPUT_FILE="/tmp/ai-maestro-github-info.txt"
> "$OUTPUT_FILE"

collect() {
    echo "$1" | tee -a "$OUTPUT_FILE"
}

# ──────────────────────────────────────────────────────────
# 1. CHECK PREREQUISITES
# ──────────────────────────────────────────────────────────
heading "1. PREREQUISITES CHECK" | collect ""
collect "$(heading '1. PREREQUISITES CHECK')"

missing=0

if command -v gh &>/dev/null; then
    collect "$(ok "gh CLI installed: $(gh --version 2>/dev/null | head -1)")"
else
    collect "$(fail "gh CLI not found. Install: https://cli.github.com/")"
    missing=1
fi

if command -v git &>/dev/null; then
    collect "$(ok "git installed: $(git --version 2>/dev/null)")"
else
    collect "$(fail "git not found.")"
    missing=1
fi

if [ "$missing" -eq 1 ]; then
    collect "$(fail "Install missing tools and re-run this script.")"
    exit 1
fi

# ──────────────────────────────────────────────────────────
# 2. GITHUB AUTHENTICATION STATUS
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '2. GITHUB AUTHENTICATION')"

AUTH_OUTPUT=$(gh auth status 2>&1) || true

if echo "$AUTH_OUTPUT" | grep -q "Logged in"; then
    AUTH_USER=$(echo "$AUTH_OUTPUT" | grep "Logged in" | grep -oP "to github\.com as \K[^ ]+" 2>/dev/null || echo "unknown")
    AUTH_SCOPES=$(echo "$AUTH_OUTPUT" | grep "Token scopes" | sed 's/.*Token scopes: //' 2>/dev/null || echo "unknown")
    AUTH_HOST=$(echo "$AUTH_OUTPUT" | grep "gh auth login" | head -1 2>/dev/null || echo "")

    collect "$(ok "Authenticated as: $AUTH_USER")"
    collect "  Scopes: $AUTH_SCOPES"

    # Check for repo push access
    if echo "$AUTH_SCOPES" | grep -q "repo"; then
        collect "$(ok "Has 'repo' scope (read/write access)")"
    else
        collect "$(warn "Missing 'repo' scope. May not have push access.")"
        collect "  Fix: gh auth login -s repo"
    fi

    # Check for workflow scope (needed for GitHub Actions)
    if echo "$AUTH_SCOPES" | grep -q "workflow"; then
        collect "$(ok "Has 'workflow' scope (can modify CI/CD)")"
    else
        collect "$(warn "Missing 'workflow' scope. Cannot modify GitHub Actions.")"
        collect "  Fix: gh auth login -s workflow"
    fi
else
    collect "$(fail "Not authenticated with GitHub")"
    collect "  Run: gh auth login"
    collect "  Then re-run this script."
fi

# ──────────────────────────────────────────────────────────
# 3. REPOSITORY DETAILS
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '3. REPOSITORY DETAILS')"

REPO_CHECK=$(gh repo view "$REPO" --json name,owner,defaultBranchRef,isFork,parent,visibility,description 2>&1) || true

if [ -n "$REPO_CHECK" ] && echo "$REPO_CHECK" | grep -q "name"; then
    DEFAULT_BRANCH=$(echo "$REPO_CHECK" | grep -oP '"name"\s*:\s*"\K[^"]+' | head -1)
    # Get default branch properly
    DEFAULT_BRANCH=$(echo "$REPO_CHECK" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('defaultBranchRef', {}).get('name', 'main'))
except: print('main')
" 2>/dev/null || echo "main")

    REPO_VISIBILITY=$(echo "$REPO_CHECK" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('visibility', 'unknown'))
except: print('unknown')
" 2>/dev/null || echo "unknown")

    IS_FORK=$(echo "$REPO_CHECK" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Yes' if d.get('isFork') else 'No')
except: print('unknown')
" 2>/dev/null || echo "unknown")

    PARENT_REPO=$(echo "$REPO_CHECK" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    p = d.get('parent')
    print(p.get('nameWithOwner', 'none') if p else 'none')
except: print('none')
" 2>/dev/null || echo "none")

    REPO_DESC=$(echo "$REPO_CHECK" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('description', 'No description') or 'No description')
except: print('No description')
" 2>/dev/null || echo "No description")

    collect "$(ok "Repository accessible")"
    collect "  URL: https://github.com/$REPO"
    collect "  Default branch: $DEFAULT_BRANCH"
    collect "  Visibility: $REPO_VISIBILITY"
    collect "  Is fork: $IS_FORK"
    collect "  Parent: $PARENT_REPO"
    collect "  Description: $REPO_DESC"
else
    collect "$(fail "Cannot access repo: $REPO")"
    collect "  Make sure the repo exists and your account has access."
fi

# ──────────────────────────────────────────────────────────
# 4. BRANCHES
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '4. EXISTING BRANCHES')"

BRANCHES=$(gh api "repos/$REPO/branches" --jq '.[].name' 2>/dev/null) || true
if [ -n "$BRANCHES" ]; then
    echo "$BRANCHES" | while read -r branch; do
        collect "  - $branch"
    done
else
    collect "  (could not list branches or none exist)"
fi

# ──────────────────────────────────────────────────────────
# 5. OPEN ISSUES / PRs
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '5. OPEN ISSUES & PULL REQUESTS')"

OPEN_ISSUES=$(gh issue list -R "$REPO" --state open --limit 10 2>/dev/null) || true
if [ -n "$OPEN_ISSUES" ]; then
    collect "  Issues:"
    echo "$OPEN_ISSUES" | while read -r line; do
        collect "    $line"
    done
else
    collect "  No open issues (or cannot access)."
fi

collect ""
OPEN_PRS=$(gh pr list -R "$REPO" --state open --limit 10 2>/dev/null) || true
if [ -n "$OPEN_PRS" ]; then
    collect "  Pull Requests:"
    echo "$OPEN_PRS" | while read -r line; do
        collect "    $line"
    done
else
    collect "  No open PRs (or cannot access)."
fi

# ──────────────────────────────────────────────────────────
# 6. LOCAL GIT CONFIG
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '6. LOCAL GIT CONFIGURATION')"

GIT_USER=$(git config --global user.name 2>/dev/null || echo "(not set)")
GIT_EMAIL=$(git config --global user.email 2>/dev/null || echo "(not set)")
GIT_EDITOR=$(git config --global core.editor 2>/dev/null || echo "(default)")
GIT_DEFAULT_BRANCH=$(git config --global init.defaultBranch 2>/dev/null || echo "(not set)")

collect "  user.name:  $GIT_USER"
collect "  user.email: $GIT_EMAIL"
collect "  core.editor: $GIT_EDITOR"
collect "  init.defaultBranch: $GIT_DEFAULT_BRANCH"

# ──────────────────────────────────────────────────────────
# 7. LOCAL REPO STATUS
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '7. LOCAL REPO STATUS (ai-maestro)')"

if [ -d "/home/prasad/ai-maestro/.git" ]; then
    collect "$(ok "Local clone exists at /home/prasad/ai-maestro")"

    REMOTES=$(cd /home/prasad/ai-maestro && git remote -v 2>/dev/null) || true
    collect "  Remotes:"
    echo "$REMOTES" | while read -r line; do
        collect "    $line"
    done

    LOCAL_BRANCH=$(cd /home/prasad/ai-maestro && git branch --show-current 2>/dev/null) || true
    collect "  Current branch: $LOCAL_BRANCH"

    LOCAL_STATUS=$(cd /home/prasad/ai-maestro && git status --short 2>/dev/null | head -20) || true
    if [ -n "$LOCAL_STATUS" ]; then
        collect "  Uncommitted changes:"
        echo "$LOCAL_STATUS" | while read -r line; do
            collect "    $line"
        done
    else
        collect "  Working tree: clean"
    fi
else
    collect "$(warn "No local clone found at /home/prasad/ai-maestro")"
fi

# ──────────────────────────────────────────────────────────
# 8. ENVIRONMENT & SECRETS DETECTION
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '8. ENVIRONMENT & SECRETS APPROACH')"

# Check for .env files
collect "  .env files detected:"
ENV_FILES=$(find /home/prasad/ai-maestro -name ".env*" -not -path "*/node_modules/*" 2>/dev/null) || true
if [ -n "$ENV_FILES" ]; then
    echo "$ENV_FILES" | while read -r f; do
        collect "    $f"
    done
else
    collect "    (none found)"
fi

# Check for docker secrets / vault references
collect "  Docker secrets / compose:"
if [ -f "/home/prasad/ai-maestro/docker-compose.yml" ] || [ -f "/home/prasad/ai-maestro/docker-compose.yaml" ]; then
    collect "    docker-compose file found"
else
    collect "    (no docker-compose file)"
fi

# Check for .gitignore patterns for secrets
collect "  .gitignore secret patterns:"
if [ -f "/home/prasad/ai-maestro/.gitignore" ]; then
    SECRET_PATTERNS=$(grep -iE "\.env|secret|key|token|credential|password" /home/prasad/ai-maestro/.gitignore 2>/dev/null) || true
    if [ -n "$SECRET_PATTERNS" ]; then
        echo "$SECRET_PATTERNS" | while read -r line; do
            collect "    $line"
        done
    else
        collect "    (no secret-related patterns found)"
    fi
else
    collect "    (no .gitignore file)"
fi

# ──────────────────────────────────────────────────────────
# 9. DEPLOYMENT TARGET DETECTION
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '9. DEPLOYMENT TARGET DETECTION')"

collect "  Infrastructure files detected:"
INFRA_FILES=$(find /home/prasad/ai-maestro -maxdepth 3 \( -name "*.tf" -o -name "*.tfvars" -o -name "Dockerfile*" -o -name "docker-compose*" -o -name "podman*" -o -name "*.kube.yaml" -o -name "*.kube.yml" -o -name "vercel.json" -o -name "netlify.toml" -o -name "railway.json" -o -name "fly.toml" -o -name "render.yaml" \) -not -path "*/node_modules/*" 2>/dev/null) || true
if [ -n "$INFRA_FILES" ]; then
    echo "$INFRA_FILES" | while read -r f; do
        collect "    $f"
    done
else
    collect "    (none found -- local dev only?)"
fi

# ──────────────────────────────────────────────────────────
# 10. CI/CD DETECTION
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '10. CI/CD PIPELINE STATUS')"

collect "  GitHub Actions workflows:"
WORKFLOW_DIR="/home/prasad/ai-maestro/.github/workflows"
if [ -d "$WORKFLOW_DIR" ]; then
    WORKFLOW_FILES=$(ls "$WORKFLOW_DIR"/*.yml "$WORKFLOW_DIR"/*.yaml 2>/dev/null) || true
    if [ -n "$WORKFLOW_FILES" ]; then
        echo "$WORKFLOW_FILES" | while read -r f; do
            collect "    $(basename "$f")"
        done
    else
        collect "    (directory exists but no workflow files)"
    fi
else
    collect "    (no .github/workflows directory)"
fi

# ──────────────────────────────────────────────────────────
# 11. Node.js / Package Manager
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '11. RUNTIME & PACKAGE MANAGER')"

NODE_VER=$(node --version 2>/dev/null || echo "not installed")
NPM_VER=$(npm --version 2>/dev/null || echo "not installed")
PNPM_VER=$(pnpm --version 2>/dev/null || echo "not installed")
YARN_VER=$(yarn --version 2>/dev/null || echo "not installed")
NVM_VER=$(nvm --version 2>/dev/null || echo "not installed")

collect "  Node.js: $NODE_VER"
collect "  npm: $NPM_VER"
collect "  pnpm: $PNPM_VER"
collect "  yarn: $YARN_VER"
collect "  nvm: $NVM_VER"

# Detect lock file
collect "  Lock file:"
for lock in pnpm-lock.yaml yarn.lock bun.lockb package-lock.json; do
    if [ -f "/home/prasad/ai-maestro/$lock" ]; then
        collect "    Found: $lock"
    fi
done

# ──────────────────────────────────────────────────────────
# INTERACTIVE PROMPTS
# ──────────────────────────────────────────────────────────
collect ""
collect "$(heading '12. YOUR PREFERENCES (interactive)')"

collect ""
collect "  Please answer the following to complete setup:"
collect ""

# Branching strategy
echo ""
echo -e "${BOLD}  [Q1] Branching strategy?${NC}"
echo "    1) Feature branches + PRs (recommended)"
echo "    2) Push directly to main"
echo "    3) Feature branches + PRs with auto-merge"
echo ""
read -rp "  Enter choice [1/2/3] (default: 1): " BRANCH_STRATEGY
BRANCH_STRATEGY=${BRANCH_STRATEGY:-1}
case "$BRANCH_STRATEGY" in
    1) collect "  Branching: Feature branches + PRs" ;;
    2) collect "  Branching: Direct push to main" ;;
    3) collect "  Branching: Feature branches + PRs with auto-merge" ;;
    *) collect "  Branching: Feature branches + PRs" ;;
esac

# Commit convention
echo ""
echo -e "${BOLD}  [Q2] Commit message style?${NC}"
echo "    1) Conventional Commits (feat:, fix:, docs:, etc.)"
echo "    2) Descriptive messages (no prefix)"
echo "    3) Emoji commits"
echo ""
read -rp "  Enter choice [1/2/3] (default: 1): " COMMIT_STYLE
COMMIT_STYLE=${COMMIT_STYLE:-1}
case "$COMMIT_STYLE" in
    1) collect "  Commits: Conventional Commits (feat|fix|docs|chore|refactor|test|ci)" ;;
    2) collect "  Commits: Descriptive messages" ;;
    3) collect "  Commits: Emoji commits" ;;
    *) collect "  Commits: Conventional Commits" ;;
esac

# Deployment target
echo ""
echo -e "${BOLD}  [Q3] Where do you plan to deploy?${NC}"
echo "    1) Local development only"
echo "    2) Docker/Podman on VPS"
echo "    3) Cloud (AWS/GCP/Azure) with Terraform"
echo "    4) Vercel / Netlify"
echo "    5) Other"
echo ""
read -rp "  Enter choice [1-5] (default: 1): " DEPLOY_TARGET
DEPLOY_TARGET=${DEPLOY_TARGET:-1}
case "$DEPLOY_TARGET" in
    1) collect "  Deploy target: Local development" ;;
    2) collect "  Deploy target: Docker/Podman on VPS" ;;
    3) collect "  Deploy target: Cloud with Terraform" ;;
    4) collect "  Deploy target: Vercel/Netlify" ;;
    5) read -rp "  Specify: " CUSTOM_DEPLOY; collect "  Deploy target: $CUSTOM_DEPLOY" ;;
    *) collect "  Deploy target: Local development" ;;
esac

# Secrets approach
echo ""
echo -e "${BOLD}  [Q4] How do you manage secrets/API keys?${NC}"
echo "    1) .env files (not committed)"
echo "    2) GitHub Secrets (for CI/CD)"
echo "    3) Vault / external secret manager"
echo "    4) Haven't decided yet"
echo ""
read -rp "  Enter choice [1-4] (default: 1): " SECRETS_APPROACH
SECRETS_APPROACH=${SECRETS_APPROACH:-1}
case "$SECRETS_APPROACH" in
    1) collect "  Secrets: .env files (not committed)" ;;
    2) collect "  Secrets: GitHub Secrets (for CI/CD)" ;;
    3) collect "  Secrets: Vault / external secret manager" ;;
    4) collect "  Secrets: Haven't decided yet" ;;
    *) collect "  Secrets: .env files" ;;
esac

# Priority areas
echo ""
echo -e "${BOLD}  [Q5] Which backlog areas to prioritize? (space-separated numbers)${NC}"
echo "    1) Terminal/WebSocket/xterm.js"
echo "    2) AI/RAG pipeline (CozoDB, embeddings, OpenAI/Anthropic)"
echo "    3) Docker/Podman deployment"
echo "    4) UI/Tailwind/framer-motion polish"
echo "    5) Testing (vitest) coverage"
echo "    6) CI/CD pipeline (GitHub Actions)"
echo "    7) Database/PostgreSQL"
echo "    8) Slack integration"
echo "    9) Terraform infrastructure"
echo "   10) All of the above"
echo ""
read -rp "  Enter choices (e.g., 1 3 5): " PRIORITIES
if [ -z "$PRIORITIES" ]; then
    PRIORITIES="10"
fi
collect "  Priority areas: $PRIORITIES"

# ──────────────────────────────────────────────────────────
# FINAL OUTPUT
# ──────────────────────────────────────────────────────────
collect ""
collect "$SEPARATOR"
collect ""
collect "  COLLECTION COMPLETE"
collect ""
collect "  Full output saved to: $OUTPUT_FILE"
collect ""
collect "  Share this with your AI agent by running:"
collect "    cat $OUTPUT_FILE"
collect ""
collect "$SEPARATOR"

echo ""
echo -e "${GREEN}${BOLD}  Done! Review the output above.${NC}"
echo -e "  Full report saved to: ${CYAN}$OUTPUT_FILE${NC}"
echo ""
echo -e "  To view/share: ${BOLD}cat $OUTPUT_FILE${NC}"
echo ""
