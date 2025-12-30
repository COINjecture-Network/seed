#!/usr/bin/env bash
set -euo pipefail

# Usage: GITHUB_TOKEN=<token> ./scripts/enable_branch_protection.sh
# This script sets recommended branch protection rules on the `main` branch
# Requires: `gh` CLI authenticated or GITHUB_TOKEN env var with repo:admin

OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
BRANCH=main

echo "Configuring branch protection for ${OWNER_REPO}:${BRANCH}"

read -r -d '' PAYLOAD <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["build-and-push","CodeQL"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_signatures": {
    "enabled": true
  }
}
JSON

echo "Payload:" >&2
echo "$PAYLOAD" | jq . >&2 || true

echo "Applying protection via gh api..."
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER_REPO}/branches/${BRANCH}/protection" \
  -f required_status_checks="$PAYLOAD" || true

echo "Finished. Verify settings in repository Settings → Branches → main."
