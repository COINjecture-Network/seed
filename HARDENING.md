# Repository Hardening Guide

This file collects concrete, repeatable steps to harden the `beanapologist/seed` repository.

1) Pre-reqs (admin account)

- Install and authenticate `gh` CLI with an admin account:

```bash
gh auth login
```

- Ensure the authenticated account has `admin` rights on `beanapologist/seed`.

2) Apply Branch Protection (recommended)

- You can run the helper script which uses the GitHub REST API to set branch protection:

```bash
# run from repository root
./scripts/enable_branch_protection.sh
```

- If the ruleset API is available for your account/org, you can create an organization-level ruleset instead:

```bash
./scripts/create_ruleset.sh
```

If either script fails with a permissions error, follow the manual steps below.

3) Manual UI steps (if API calls fail)

- Go to: Settings → Branches → Add rule
- Target branch: `main`
- Require pull request reviews before merging
  - Require at least 1 approving review
  - Require review from CODEOWNERS
- Require status checks to pass before merging
  - Add checks: the CI check names are the workflow job names. Common ones in this repo are:
    - `build-and-push` (container build)
    - `CodeQL` (CodeQL analysis)
  - Check "Require branches to be up to date before merging"
- Require signed commits (if available)
  - Enable "Require signed commits" if your org supports it
- Enforce linear history (disallow merge commits) and block force pushes

4) Release signing & checksums

- Add `GPG_PRIVATE_KEY` secret (base64-encoded ASCII-armored private key) to repository Secrets for automatic signing when a release is published.
- On release, `scripts/generate_checksums.sh` will create `checksums.txt` and `.github/workflows/sign-release.yml` will sign (if key present) and upload checksums.

5) Commit signing and PR enforcement

- We added `.github/workflows/verify-commit-signatures.yml` to ensure PR commits are GPG-signed. To enforce this, add it as a required check in branch protection.

6) Verify protections

```bash
# Show current branch protection (may require admin token scopes)
gh api --method GET -H "Accept: application/vnd.github+json" \
  "/repos/beanapologist/seed/branches/main/protection" | jq .
```

7) If you want me to run the create/apply scripts here, I can — but the `gh` token in this environment must have the required admin scopes. If you prefer to run locally, run the scripts above and paste any API error here; I'll adapt the payload automatically.

8) Optional: enable automated monitoring

- Add a lightweight Action that runs nightly to check whether branch protections and rulesets are present; it can open an issue if misconfigured. I can add that if you want.

---

Last updated: December 30, 2025
