"""Render EcoMech ecological process YAML files to HTML pages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, select_autoescape

# ---------------------------------------------------------------------------
# Ontology browser URL builders
# ---------------------------------------------------------------------------

_TERM_URL_TEMPLATES: dict[str, str] = {
    "ENVO": (
        "https://www.ebi.ac.uk/ols4/ontologies/envo/terms"
        "?iri=http://purl.obolibrary.org/obo/ENVO_{local}"
    ),
    "GO": (
        "https://www.ebi.ac.uk/ols4/ontologies/go/terms"
        "?iri=http://purl.obolibrary.org/obo/GO_{local}"
    ),
    "NCBITaxon": (
        "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={local}"
    ),
    "PATO": (
        "https://www.ebi.ac.uk/ols4/ontologies/pato/terms"
        "?iri=http://purl.obolibrary.org/obo/PATO_{local}"
    ),
    "ECTO": (
        "https://www.ebi.ac.uk/ols4/ontologies/ecto/terms"
        "?iri=http://purl.obolibrary.org/obo/ECTO_{local}"
    ),
    "CHEBI": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:{local}",
    "UBERON": (
        "https://www.ebi.ac.uk/ols4/ontologies/uberon/terms"
        "?iri=http://purl.obolibrary.org/obo/UBERON_{local}"
    ),
}


def term_url(curie: str) -> str:
    """Return an ontology browser URL for a CURIE, or '#' if unknown."""
    if not curie or ":" not in curie:
        return "#"
    prefix, local = curie.split(":", 1)
    template = _TERM_URL_TEMPLATES.get(prefix)
    return template.format(local=local) if template else "#"


def reference_url(ref: str) -> str:
    """Return a URL for a literature reference identifier."""
    if ref.startswith("PMID:"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{ref[5:]}/"
    if ref.startswith("DOI:"):
        return f"https://doi.org/{ref[4:]}"
    return "#"


# ---------------------------------------------------------------------------
# Jinja2 template (embedded)
# ---------------------------------------------------------------------------

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ process.name }} — EcoMech</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      color: #1a1a1a;
      background: #f7f9f7;
    }

    a { color: #2d6a4f; text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* ── Layout ── */
    .site-header {
      background: #1b4332;
      color: #fff;
      padding: 0.5rem 2rem;
      font-size: 0.85rem;
      letter-spacing: 0.04em;
    }
    .site-header a { color: #95d5b2; }

    .page-hero {
      background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
      color: #fff;
      padding: 2.5rem 2rem 2rem;
    }
    .page-hero .process-term {
      display: inline-block;
      background: rgba(255,255,255,0.15);
      border-radius: 4px;
      padding: 0.15rem 0.6rem;
      font-size: 0.8rem;
      font-family: monospace;
      margin-bottom: 0.75rem;
    }
    .page-hero h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.4rem; }
    .page-hero .scale-badge {
      display: inline-block;
      background: rgba(255,255,255,0.2);
      border-radius: 20px;
      padding: 0.15rem 0.75rem;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 1rem;
    }
    .page-hero .description { max-width: 820px; opacity: 0.92; }
    .page-hero .synonyms {
      margin-top: 0.75rem;
      font-size: 0.85rem;
      opacity: 0.75;
    }

    .main { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }

    /* ── Section cards ── */
    .section { margin-bottom: 2rem; }
    .section-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #1b4332;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border-bottom: 2px solid #d8f3dc;
      padding-bottom: 0.4rem;
      margin-bottom: 1rem;
    }

    .card {
      background: #fff;
      border: 1px solid #e0ece4;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
    }
    .card-title {
      font-size: 1rem;
      font-weight: 600;
      color: #1b4332;
      margin-bottom: 0.5rem;
    }
    .card-desc { color: #444; margin-bottom: 0.75rem; }

    /* ── Badges ── */
    .badge {
      display: inline-block;
      border-radius: 4px;
      padding: 0.1rem 0.5rem;
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-right: 0.35rem;
      margin-bottom: 0.25rem;
    }
    .badge-envo  { background: #d8f3dc; color: #1b4332; }
    .badge-go    { background: #dbeafe; color: #1e40af; }
    .badge-taxon { background: #fef3c7; color: #92400e; }
    .badge-pato  { background: #ede9fe; color: #5b21b6; }
    .badge-ecto  { background: #fee2e2; color: #991b1b; }
    .badge-chebi { background: #f0fdf4; color: #166534; }
    .badge-scale { background: #e0f2fe; color: #0c4a6e; }

    .support-badge {
      border-radius: 4px;
      padding: 0.1rem 0.5rem;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .support-SUPPORT { background: #bbf7d0; color: #14532d; }
    .support-REFUTE  { background: #fecaca; color: #7f1d1d; }
    .support-PARTIAL { background: #fef9c3; color: #713f12; }
    .support-NO_EVIDENCE { background: #f3f4f6; color: #4b5563; }

    .driver-badge {
      border-radius: 20px;
      padding: 0.1rem 0.6rem;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .driver-ABIOTIC      { background: #e0f2fe; color: #0c4a6e; }
    .driver-BIOTIC       { background: #fef3c7; color: #92400e; }
    .driver-ANTHROPOGENIC { background: #fee2e2; color: #991b1b; }
    .driver-CLIMATE      { background: #ede9fe; color: #5b21b6; }
    .driver-GEOCHEMICAL  { background: #d8f3dc; color: #1b4332; }

    .intervention-badge {
      border-radius: 20px;
      padding: 0.1rem 0.6rem;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .intervention-RESTORATION { background: #d8f3dc; color: #1b4332; }
    .intervention-MANAGEMENT  { background: #dbeafe; color: #1e40af; }
    .intervention-PROTECTION  { background: #fef3c7; color: #92400e; }
    .intervention-MITIGATION  { background: #ede9fe; color: #5b21b6; }
    .intervention-REMOVAL     { background: #fecaca; color: #7f1d1d; }
    .intervention-MONITORING  { background: #f3f4f6; color: #374151; }

    /* ── Term rows ── */
    .term-row {
      display: flex;
      align-items: baseline;
      gap: 0.5rem;
      margin-bottom: 0.35rem;
      flex-wrap: wrap;
    }
    .term-id {
      font-family: monospace;
      font-size: 0.78rem;
      color: #6b7280;
    }

    /* ── Causal edges ── */
    .causal-edge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.4rem 0.75rem;
      background: #f0fdf4;
      border-left: 3px solid #52b788;
      border-radius: 0 4px 4px 0;
      margin-bottom: 0.4rem;
      font-size: 0.88rem;
    }
    .causal-edge .subject { font-weight: 600; }
    .causal-edge .predicate {
      color: #2d6a4f;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 0.1rem 0.4rem;
      background: #d8f3dc;
      border-radius: 4px;
    }
    .causal-edge .object { font-style: italic; }

    /* ── Evidence ── */
    details.evidence-block {
      margin-top: 0.6rem;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      overflow: hidden;
    }
    details.evidence-block summary {
      cursor: pointer;
      padding: 0.4rem 0.75rem;
      background: #f9fafb;
      font-size: 0.82rem;
      color: #374151;
      list-style: none;
      user-select: none;
    }
    details.evidence-block summary::before {
      content: "▶ ";
      font-size: 0.65rem;
      color: #9ca3af;
    }
    details.evidence-block[open] summary::before { content: "▼ "; }
    .evidence-body {
      padding: 0.75rem 1rem;
      background: #fff;
    }
    .evidence-item { margin-bottom: 0.75rem; }
    .evidence-item:last-child { margin-bottom: 0; }
    .evidence-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 0.4rem;
    }
    .evidence-ref a {
      font-weight: 600;
      font-size: 0.85rem;
      color: #2d6a4f;
    }
    .evidence-source {
      font-size: 0.7rem;
      color: #6b7280;
      background: #f3f4f6;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
    }
    blockquote.snippet {
      border-left: 3px solid #52b788;
      padding: 0.4rem 0.75rem;
      margin: 0.35rem 0;
      font-size: 0.85rem;
      color: #374151;
      font-style: italic;
      background: #f0fdf4;
      border-radius: 0 4px 4px 0;
    }
    .explanation {
      font-size: 0.82rem;
      color: #6b7280;
      margin-top: 0.3rem;
    }

    /* ── Habitat list ── */
    .habitat-item {
      display: flex;
      align-items: baseline;
      gap: 0.6rem;
      padding: 0.5rem 0;
      border-bottom: 1px solid #f3f4f6;
    }
    .habitat-item:last-child { border-bottom: none; }

    /* ── Sub-sections inside mechanism cards ── */
    .subsection { margin-top: 1rem; }
    .subsection-title {
      font-size: 0.78rem;
      font-weight: 700;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.4rem;
    }

    /* ── Abiotic conditions ── */
    .abiotic-row {
      padding: 0.35rem 0.75rem;
      background: #eff6ff;
      border-radius: 4px;
      margin-bottom: 0.3rem;
      font-size: 0.88rem;
    }
    .abiotic-value {
      font-family: monospace;
      font-size: 0.78rem;
      background: #dbeafe;
      color: #1e40af;
      padding: 0.05rem 0.4rem;
      border-radius: 3px;
      margin-left: 0.4rem;
    }

    footer {
      text-align: center;
      padding: 2rem;
      font-size: 0.8rem;
      color: #9ca3af;
      border-top: 1px solid #e5e7eb;
      margin-top: 2rem;
    }
  </style>
</head>
<body>

<header class="site-header">
  <a href="../../index.html">EcoMech</a> &rsaquo;
  <a href="../index.html">Processes</a> &rsaquo;
  {{ process.name }}
</header>

<div class="page-hero">
  {% if process.process_term %}
  <div class="process-term">
    <a href="{{ term_url(process.process_term.id) }}" style="color:#95d5b2;"
       target="_blank" rel="noopener">
      {{ process.process_term.id }}
    </a>
    &nbsp;{{ process.process_term.label }}
  </div>
  {% endif %}
  <h1>{{ process.name }}</h1>
  {% if process.ecological_scale %}
  <div class="scale-badge">{{ process.ecological_scale }} scale</div>
  {% endif %}
  <div class="description">{{ process.description }}</div>
  {% if process.synonyms %}
  <div class="synonyms">Also known as: {{ process.synonyms | join(", ") }}</div>
  {% endif %}
</div>

<main class="main">

  {# ── Mechanisms ── #}
  {% if process.mechanisms %}
  <section class="section">
    <h2 class="section-title">Mechanisms</h2>
    {% for mech in process.mechanisms %}
    <div class="card">
      <div class="card-title">{{ mech.name }}</div>
      {% if mech.description %}<div class="card-desc">{{ mech.description }}</div>{% endif %}

      {# Biological processes #}
      {% if mech.biological_processes %}
      <div class="subsection">
        <div class="subsection-title">Biological Processes</div>
        {% for bp in mech.biological_processes %}
        <div class="term-row">
          <a href="{{ term_url(bp.term.id) }}" target="_blank" rel="noopener">
            <span class="badge badge-go">GO</span>
          </a>
          <span>{{ bp.term.label }}</span>
          <span class="term-id">{{ bp.term.id }}</span>
        </div>
        {% if bp.evidence %}
        <details class="evidence-block">
          <summary>{{ bp.evidence | length }} evidence item{{ 's' if bp.evidence|length != 1 }}</summary>
          <div class="evidence-body">
            {% for ev in bp.evidence %}{{ _render_evidence(ev) }}{% endfor %}
          </div>
        </details>
        {% endif %}
        {% endfor %}
      </div>
      {% endif %}

      {# Ecological processes #}
      {% if mech.ecological_processes %}
      <div class="subsection">
        <div class="subsection-title">Ecological Processes</div>
        {% for ep in mech.ecological_processes %}
        <div class="term-row">
          <a href="{{ term_url(ep.term.id) }}" target="_blank" rel="noopener">
            <span class="badge badge-envo">ENVO</span>
          </a>
          <span>{{ ep.term.label }}</span>
          <span class="term-id">{{ ep.term.id }}</span>
        </div>
        {% if ep.evidence %}
        <details class="evidence-block">
          <summary>{{ ep.evidence | length }} evidence item{{ 's' if ep.evidence|length != 1 }}</summary>
          <div class="evidence-body">
            {% for ev in ep.evidence %}{{ _render_evidence(ev) }}{% endfor %}
          </div>
        </details>
        {% endif %}
        {% endfor %}
      </div>
      {% endif %}

      {# Chemical entities #}
      {% if mech.chemical_entities %}
      <div class="subsection">
        <div class="subsection-title">Chemical Entities</div>
        {% for ce in mech.chemical_entities %}
        <div class="term-row">
          <a href="{{ term_url(ce.term.id) }}" target="_blank" rel="noopener">
            <span class="badge badge-chebi">CHEBI</span>
          </a>
          <span>{{ ce.term.label }}</span>
          <span class="term-id">{{ ce.term.id }}</span>
        </div>
        {% if ce.evidence %}
        <details class="evidence-block">
          <summary>{{ ce.evidence | length }} evidence item{{ 's' if ce.evidence|length != 1 }}</summary>
          <div class="evidence-body">
            {% for ev in ce.evidence %}{{ _render_evidence(ev) }}{% endfor %}
          </div>
        </details>
        {% endif %}
        {% endfor %}
      </div>
      {% endif %}

      {# Taxa involved #}
      {% if mech.taxa_involved %}
      <div class="subsection">
        <div class="subsection-title">Taxa Involved</div>
        {% for td in mech.taxa_involved %}
        <div class="term-row">
          <a href="{{ term_url(td.taxon.id) }}" target="_blank" rel="noopener">
            <span class="badge badge-taxon">NCBITaxon</span>
          </a>
          <span><em>{{ td.taxon.label }}</em></span>
          <span class="term-id">{{ td.taxon.id }}</span>
          {% if td.role %}<span class="badge badge-scale" style="font-size:0.68rem;">{{ td.role }}</span>{% endif %}
        </div>
        {% if td.description %}<div style="font-size:0.83rem;color:#555;margin-left:0.5rem;margin-bottom:0.25rem;">{{ td.description }}</div>{% endif %}
        {% endfor %}
      </div>
      {% endif %}

      {# Abiotic conditions #}
      {% if mech.abiotic_conditions %}
      <div class="subsection">
        <div class="subsection-title">Abiotic Conditions</div>
        {% for ac in mech.abiotic_conditions %}
        <div class="abiotic-row">
          {% if ac.envo_condition_term %}
          <a href="{{ term_url(ac.envo_condition_term.id) }}" target="_blank" rel="noopener">
            <span class="badge badge-envo" style="margin-right:0.3rem;">ENVO</span>
          </a>
          <strong>{{ ac.envo_condition_term.label }}</strong>
          {% endif %}
          {% if ac.condition_value %}<span class="abiotic-value">{{ ac.condition_value }}</span>{% endif %}
          {% if ac.description %} — <span style="font-size:0.83rem;color:#555;">{{ ac.description }}</span>{% endif %}
        </div>
        {% endfor %}
      </div>
      {% endif %}

      {# Causal edges #}
      {% if mech.causal_edges %}
      <div class="subsection">
        <div class="subsection-title">Causal Relationships</div>
        {% for edge in mech.causal_edges %}
        <div class="causal-edge">
          <span class="subject">{{ edge.subject }}</span>
          <span class="predicate">{{ edge.predicate }}</span>
          <span class="object">{{ edge.object }}</span>
        </div>
        {% if edge.description %}<div style="font-size:0.8rem;color:#6b7280;margin-left:0.75rem;margin-bottom:0.25rem;">{{ edge.description }}</div>{% endif %}
        {% endfor %}
      </div>
      {% endif %}

      {# Mechanism-level evidence #}
      {% if mech.evidence %}
      <div class="subsection">
        <details class="evidence-block">
          <summary>Mechanism evidence ({{ mech.evidence | length }} item{{ 's' if mech.evidence|length != 1 }})</summary>
          <div class="evidence-body">
            {% for ev in mech.evidence %}{{ _render_evidence(ev) }}{% endfor %}
          </div>
        </details>
      </div>
      {% endif %}

    </div>
    {% endfor %}
  </section>
  {% endif %}

  {# ── Indicators ── #}
  {% if process.indicators %}
  <section class="section">
    <h2 class="section-title">Ecological Indicators</h2>
    {% for ind in process.indicators %}
    <div class="card">
      <div class="card-title">{{ ind.name }}</div>
      {% if ind.description %}<div class="card-desc">{{ ind.description }}</div>{% endif %}
      <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.5rem;align-items:center;">
        {% if ind.indicator_term %}
        <a href="{{ term_url(ind.indicator_term.id) }}" target="_blank" rel="noopener">
          <span class="badge badge-pato">PATO</span>
        </a>
        <span style="font-size:0.88rem;">{{ ind.indicator_term.label }}</span>
        <span class="term-id">{{ ind.indicator_term.id }}</span>
        {% endif %}
        {% if ind.frequency %}<span class="badge badge-scale">{{ ind.frequency }}</span>{% endif %}
        {% if ind.temporality %}<span class="badge" style="background:#fdf2f8;color:#701a75;">{{ ind.temporality }}</span>{% endif %}
      </div>
      {% if ind.measurement %}
      <div style="font-size:0.83rem;color:#374151;margin-bottom:0.5rem;">
        <strong>Measurement:</strong> <code>{{ ind.measurement }}</code>
      </div>
      {% endif %}
      {% if ind.evidence %}
      <details class="evidence-block">
        <summary>{{ ind.evidence | length }} evidence item{{ 's' if ind.evidence|length != 1 }}</summary>
        <div class="evidence-body">
          {% for ev in ind.evidence %}{{ _render_evidence(ev) }}{% endfor %}
        </div>
      </details>
      {% endif %}
    </div>
    {% endfor %}
  </section>
  {% endif %}

  {# ── Drivers ── #}
  {% if process.drivers %}
  <section class="section">
    <h2 class="section-title">Drivers &amp; Stressors</h2>
    {% for drv in process.drivers %}
    <div class="card">
      <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;flex-wrap:wrap;">
        <span class="card-title" style="margin-bottom:0;">{{ drv.name }}</span>
        {% if drv.driver_type %}
        <span class="driver-badge driver-{{ drv.driver_type }}">{{ drv.driver_type }}</span>
        {% endif %}
      </div>
      {% if drv.description %}<div class="card-desc">{{ drv.description }}</div>{% endif %}
      {% if drv.driver_term %}
      <div class="term-row" style="margin-bottom:0.5rem;">
        <a href="{{ term_url(drv.driver_term.id) }}" target="_blank" rel="noopener">
          <span class="badge badge-ecto">ECTO</span>
        </a>
        <span style="font-size:0.88rem;">{{ drv.driver_term.label }}</span>
        <span class="term-id">{{ drv.driver_term.id }}</span>
      </div>
      {% endif %}
      {% if drv.chemical_agent %}
      <div class="term-row" style="margin-bottom:0.5rem;">
        <a href="{{ term_url(drv.chemical_agent.id) }}" target="_blank" rel="noopener">
          <span class="badge badge-chebi">CHEBI</span>
        </a>
        <span style="font-size:0.88rem;">{{ drv.chemical_agent.label }}</span>
        <span class="term-id">{{ drv.chemical_agent.id }}</span>
      </div>
      {% endif %}
      {% if drv.evidence %}
      <details class="evidence-block">
        <summary>{{ drv.evidence | length }} evidence item{{ 's' if drv.evidence|length != 1 }}</summary>
        <div class="evidence-body">
          {% for ev in drv.evidence %}{{ _render_evidence(ev) }}{% endfor %}
        </div>
      </details>
      {% endif %}
    </div>
    {% endfor %}
  </section>
  {% endif %}

  {# ── Interventions ── #}
  {% if process.interventions %}
  <section class="section">
    <h2 class="section-title">Interventions</h2>
    {% for iv in process.interventions %}
    <div class="card">
      <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;flex-wrap:wrap;">
        <span class="card-title" style="margin-bottom:0;">{{ iv.name }}</span>
        {% if iv.intervention_type %}
        <span class="intervention-badge intervention-{{ iv.intervention_type }}">{{ iv.intervention_type }}</span>
        {% endif %}
      </div>
      {% if iv.description %}<div class="card-desc">{{ iv.description }}</div>{% endif %}
      {% if iv.intervention_term %}
      <div class="term-row" style="margin-bottom:0.5rem;">
        <span class="badge badge-envo">Term</span>
        <span style="font-size:0.88rem;">{{ iv.intervention_term.label }}</span>
        <span class="term-id">{{ iv.intervention_term.id }}</span>
      </div>
      {% endif %}
      {% if iv.evidence %}
      <details class="evidence-block">
        <summary>{{ iv.evidence | length }} evidence item{{ 's' if iv.evidence|length != 1 }}</summary>
        <div class="evidence-body">
          {% for ev in iv.evidence %}{{ _render_evidence(ev) }}{% endfor %}
        </div>
      </details>
      {% endif %}
    </div>
    {% endfor %}
  </section>
  {% endif %}

  {# ── Habitat context ── #}
  {% if process.habitat_context %}
  <section class="section">
    <h2 class="section-title">Habitat Context</h2>
    <div class="card">
      {% for hc in process.habitat_context %}
      <div class="habitat-item">
        <a href="{{ term_url(hc.habitat_term.id) }}" target="_blank" rel="noopener">
          <span class="badge badge-envo">ENVO</span>
        </a>
        <strong>{{ hc.habitat_term.label }}</strong>
        <span class="term-id">{{ hc.habitat_term.id }}</span>
        {% if hc.description %} — <span style="font-size:0.88rem;color:#555;">{{ hc.description }}</span>{% endif %}
      </div>
      {% endfor %}
    </div>
  </section>
  {% endif %}

</main>

<footer>
  EcoMech &mdash; Ecological Process Mechanisms Knowledge Base
  {% if process.creation_date %}
  &mdash; Entry created {{ process.creation_date[:10] }}
  {% endif %}
</footer>

</body>
</html>
"""

# Jinja2 macro rendered via a helper (macros can't be called from globals,
# so we render evidence items via a callable filter instead).
_EVIDENCE_ITEM_TEMPLATE = """\
<div class="evidence-item">
  <div class="evidence-meta">
    <span class="evidence-ref">
      <a href="{{ ref_url }}" target="_blank" rel="noopener">{{ ref }}</a>
    </span>
    {% if supports %}
    <span class="support-badge support-{{ supports }}">{{ supports }}</span>
    {% endif %}
    {% if source %}
    <span class="evidence-source">{{ source }}</span>
    {% endif %}
  </div>
  {% if snippet %}
  <blockquote class="snippet">&ldquo;{{ snippet }}&rdquo;</blockquote>
  {% endif %}
  {% if explanation %}
  <div class="explanation">{{ explanation }}</div>
  {% endif %}
</div>
"""


def _make_env() -> Environment:
    env = Environment(autoescape=select_autoescape(["html"]))
    env.globals["term_url"] = term_url
    env.globals["reference_url"] = reference_url

    ev_tmpl = env.from_string(_EVIDENCE_ITEM_TEMPLATE)

    def _render_evidence(ev: dict[str, Any]) -> str:
        ref = ev.get("reference", "")
        return ev_tmpl.render(
            ref=ref,
            ref_url=reference_url(ref),
            supports=ev.get("supports", ""),
            source=ev.get("evidence_source", ""),
            snippet=ev.get("snippet", ""),
            explanation=ev.get("explanation", ""),
        )

    env.globals["_render_evidence"] = _render_evidence
    return env


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_process(
    input_path: str | Path,
    output_dir: str | Path = "pages/processes",
) -> Path:
    """Render an EcologicalProcess YAML file to an HTML page.

    Args:
        input_path: Path to the KB YAML file.
        output_dir: Directory to write the HTML file into.

    Returns:
        Path to the generated HTML file.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = yaml.safe_load(input_path.read_text())

    env = _make_env()
    template = env.from_string(_TEMPLATE)
    html = template.render(process=data)

    output_path = output_dir / f"{input_path.stem}.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m ecomech.render.render <path/to/process.yaml>", file=sys.stderr)
        sys.exit(1)

    for arg in sys.argv[1:]:
        out = render_process(arg)
        print(f"Rendered: {out}")


if __name__ == "__main__":
    main()
