# EcoMech Workplan

## Phase 1 — Infrastructure (Weeks 1–4)

1. **Install and verify toolchain**: `just install`, run `just qc` on the nitrogen cycling entry with real PMIDs fetched
2. **Finalize schema**: Validate the LinkML schema generates clean Python datamodels (`just gen-all`); refine enums and slots based on first curation experience
3. **HTML renderer**: Implement `src/ecomech/render/render.py` (Jinja2 templates → browsable process pages), following dismech's pattern
4. **Compliance dashboard**: Implement field-coverage analysis (`src/ecomech/analysis/compliance.py`)
5. **CI/CD**: GitHub Actions workflow for `just qc` on every PR

## Phase 2 — Seed Curation (Weeks 5–12)

Prioritize **30–50 foundational ecological processes** covering the major biogeochemical cycles and ecosystem function categories:

| Category | Target Processes |
|---|---|
| Nutrient cycles | Nitrogen cycling, phosphorus cycling, carbon cycling, sulfur cycling |
| Primary production | Terrestrial NPP, marine primary production, benthic production |
| Decomposition | Litter decomposition, dissolved organic matter mineralization |
| Trophic processes | Herbivory, predation, detritivory, trophic cascades |
| Symbioses | Mycorrhizal association, root nodule symbiosis, coral-zooxanthellae |
| Disturbance/succession | Wildfire succession, gap dynamics, flood pulse |
| Biogeochemical coupling | Redox dynamics, methane cycling, iron cycling |
| Ecosystem services | Pollination, seed dispersal, water filtration, carbon sequestration |

For each process:
- Find ENVO term in the ENVO:02500000 subtree
- Curate 3–5 mechanisms backed by ≥2 PMIDs each
- 3–5 quantitative indicators
- 3–5 key drivers
- 2–3 validated interventions

## Phase 3 — Module Library (Months 3–4)

Build reusable **mechanism modules** in `kb/modules/` for conserved components:
- Decomposition cascade
- Trophic amplification
- Redox ladder
- Microbial loop
- Stoichiometric homeostasis
- Threshold/regime shift dynamics

## Phase 4 — Tooling Expansion (Months 4–6)

1. **Network export**: CX2 / KGX graph export for visualization (adapt `dismech-cx2`)
2. **OAK-powered curation skill**: `/curate` Claude Code skill for automated ENVO term lookup, PubMed search, and YAML drafting
3. **ENVO hierarchy browser**: Interactive browser showing which ENVO process subtrees are curated vs. uncurated
4. **Cross-database ingestion**: Pull structured data from GBIF (species traits), LTER (long-term datasets), TRY (plant traits), GloNAF (invasive species)
5. **Embedding explorer**: UMAP/TSNE visualization of process similarity

## Phase 5 — Community & Scale (Months 6–12)

1. Open community curation via GitHub PRs with automated validation
2. Target 200+ ecological processes covering all major biomes
3. Integrate with Earth System ontologies (SWEET) and biodiversity informatics (DwC)
4. KGX export for integration with Monarch Knowledge Graph
5. Prioritization dashboard showing uncurated ENVO processes (analogous to dismech's MONDO coverage dashboard)

## Immediate Next Steps

```bash
cd ecomech
just install
# Replace placeholder snippets in Nitrogen_Cycling.yaml with real PMIDs:
just fetch-reference PMID:15006420
just fetch-reference PMID:16957253
just fetch-reference PMID:11397943
just fetch-reference PMID:9651482
# Then update snippets to exact verbatim quotes and run:
just qc
```
