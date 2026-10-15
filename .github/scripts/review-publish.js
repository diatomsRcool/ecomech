// review-publish.js
// Posts a structured PR review from the review agent's JSON output.
// Called from the publish job in review.yaml.

"use strict";

const SEVERITY_ICON = { error: "🔴", warning: "🟡", note: "🔵" };

/** Format findings array as a markdown list. */
function formatFindings(findings) {
  if (!findings || findings.length === 0) return "_No findings._";
  return findings
    .map((f) => {
      const icon = SEVERITY_ICON[f.severity] ?? "⚪";
      const loc = f.file
        ? ` \`${f.file}${f.line != null ? `:${f.line}` : ""}\``
        : "";
      return `- ${icon}${loc} ${f.message}`;
    })
    .join("\n");
}

/** Format checklist as GitHub markdown checkboxes. */
function formatChecklist(checklist) {
  if (!checklist || Object.keys(checklist).length === 0) return "_No checklist._";
  return Object.entries(checklist)
    .map(([key, value]) => `- [${value ? "x" : " "}] ${key}`)
    .join("\n");
}

/**
 * Post the agent's review to the PR.
 *
 * @param {object} github    - Octokit client from github-script
 * @param {string} repo      - "owner/repo" string
 * @param {number} prNumber  - Pull request number
 * @param {object} result    - Parsed JSON from review_output.json
 * @param {object} options   - { appToken?: string }
 */
async function publish(github, repo, prNumber, result, options = {}) {
  const verdict = result.verdict ?? "request_changes";
  const summary = result.summary ?? "_No summary provided._";
  const checklist = result.checklist ?? {};
  const findings = result.findings ?? [];

  const hasErrors = findings.some((f) => f.severity === "error");
  const hasWarnings = findings.some((f) => f.severity === "warning");
  const statusLine = verdict === "approve"
    ? "**Result: Approved** — no blocking issues found."
    : `**Result: Changes requested** — ${hasErrors ? "errors" : "warnings"} need to be resolved.`;

  const body = [
    "## EcoMech automated review",
    "",
    statusLine,
    "",
    "### Checklist",
    formatChecklist(checklist),
    "",
    "### Summary",
    summary,
    "",
    "### Findings",
    formatFindings(findings),
    "",
    "---",
    "_Automated review by Claude. A human must approve before merging._",
  ].join("\n");

  const [owner, repoName] = repo.split("/");
  const event = verdict === "approve" ? "APPROVE" : "REQUEST_CHANGES";

  if (options.appToken && event === "APPROVE") {
    // Use the app token so the bot can approve its own PRs
    const { Octokit } = require("@octokit/core");
    const appOctokit = new Octokit({ auth: options.appToken });
    await appOctokit.request(
      "POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews",
      { owner, repo: repoName, pull_number: prNumber, event, body }
    );
  } else {
    await github.rest.pulls.createReview({
      owner,
      repo: repoName,
      pull_number: prNumber,
      event,
      body,
    });
  }

  console.log(`Posted ${event} review on PR #${prNumber}`);
}

module.exports = { publish };
