#!/usr/bin/env bash
# Parse owner/repo from a GitHub git remote (supports dotted repo names, e.g. trainer.skill).
# Source from trainer_pr_review_post.sh / trainer_pr_review_gate_rerun.sh — do not execute directly.

trainer_gh_repo_from_remote() {
  local remote="${1:-}"
  local stripped="${remote%.git}"
  if [[ "$stripped" =~ github\.com[:/]([^/]+/[^/]+)$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}
