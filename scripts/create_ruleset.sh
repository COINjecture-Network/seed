#!/usr/bin/env bash
set -euo pipefail

# Create a repository ruleset via GitHub REST API using gh CLI
# Usage: GITHUB_TOKEN=<token> ./scripts/create_ruleset.sh
# Requires: gh CLI logged in with sufficient permissions (admin)

OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Creating ruleset for ${OWNER_REPO}"

read -r -d '' PAYLOAD <<'JSON'
{
  "name": "Enforce secure merges and signed commits",
  "target": "branch",
  "conditions": {
    "branches": ["refs/heads/main"],
    "enforcement": "always"
  },
  "enforcement": "always",
  "rules": [
    {
      "type": "required_pull_request_reviews",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict": true,
        "contexts": ["build-and-push", "CodeQL"]
      }
    },
    {
      "type": "required_linear_history",
      "parameters": {}
    },
    {
      "type": "block_force_push",
      "parameters": {}
    },
    {
      "type": "required_signatures",
      "parameters": {}
    },
    {
      "type": "restrict_pushes",
      "parameters": {
        "teams": [],
        "users": ["beanapologist"]
      }
    }
  ]
}
JSON

echo "Payload:" >&2
echo "$PAYLOAD" | jq . >&2 || true

echo "Creating ruleset via gh api..."
gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER_REPO}/rulesets" \
  -f body="$PAYLOAD"

echo "Ruleset creation requested. Verify in repository Settings → Rulesets."
