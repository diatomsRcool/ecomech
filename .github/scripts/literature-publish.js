// literature-publish.js
// Creates GitHub issues from the literature-scan agent's JSON output.
// Called from the publish job in literature-scan.yaml.

"use strict";

/** Remove @ mentions and trim to a safe length. */
function clean(text, max = 600) {
  return String(text ?? "").replace(/@\S+/g, "[mention]").slice(0, max).trim();
}

/** Collapse multiline text to one line. */
function oneLine(text, max = 120) {
  return String(text ?? "").replace(/\s+/g, " ").slice(0, max).trim();
}

/** Format text as a blockquote. */
function quoted(text) {
  return String(text ?? "")
    .split("\n")
    .map((line) => `> ${line}`)
    .join("\n");
}

/** Build a GitHub issue object for a lead. */
function issueFor(lead, paper) {
  const isPreprint = String(lead.paper).startsWith("PPR:");
  const hasEntry = Boolean(lead.entry);

  const labels = ["curation"];
  labels.push(hasEntry ? "low_effort" : "high_effort");
  if (isPreprint) labels.push("preprint");

  const entryLine = hasEntry
    ? `**Related entry:** \`${lead.entry}\``
    : "**New entry** — no existing process file covers this topic.";

  const body = [
    `## Literature lead: ${oneLine(lead.name)}`,
    "",
    `**Source:** ${lead.paper}`,
    entryLine,
    "",
    "### Why this paper was selected",
    clean(lead.assessment, 800),
    "",
    "### Abstract",
    quoted(clean(paper.abstract ?? "_Abstract not available._", 1500)),
    "",
    "---",
    "_Filed by the weekly EcoMech literature scan._",
    "_To curate this entry, comment_ `@claude curate this`.",
  ].join("\n");

  return {
    title: `[Literature] ${oneLine(lead.name, 100)}`,
    labels,
    body,
  };
}

/** Return true if an open issue already mentions this paper ID. */
async function alreadyFiled(github, repo, paperId) {
  const { data } = await github.rest.search.issuesAndPullRequests({
    q: `repo:${repo} is:issue is:open "${paperId}" in:body`,
    per_page: 5,
  });
  return data.total_count > 0;
}

/**
 * Create GitHub issues for each agent-selected lead.
 *
 * @param {object} github  - Octokit client from github-script
 * @param {string} repo    - "owner/repo" string
 * @param {object} result  - Parsed JSON from scan_output.json {"leads": [...]}
 * @param {object} packet  - Parsed JSON from literature_packet.json {"papers": [...]}
 * @param {object} options - { maxIssues: number }
 */
async function publish(github, repo, result, packet, options = {}) {
  const maxIssues = Math.min(options.maxIssues ?? 5, 10);
  const leads = (result.leads ?? []).slice(0, maxIssues);
  const paperMap = Object.fromEntries(
    (packet.papers ?? []).map((p) => [p.id, p])
  );

  let filed = 0;
  for (const lead of leads) {
    if (await alreadyFiled(github, repo, lead.paper)) {
      console.log(`Skipping ${lead.paper} — already has an open issue`);
      continue;
    }
    const paper = paperMap[lead.paper] ?? {};
    const issue = issueFor(lead, paper);
    const [owner, repoName] = repo.split("/");
    await github.rest.issues.create({ owner, repo: repoName, ...issue });
    console.log(`Filed: ${issue.title}`);
    filed++;
  }
  console.log(`Total issues filed: ${filed}`);
}

module.exports = { publish };
