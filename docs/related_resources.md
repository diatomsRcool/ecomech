# EcoMech: Relationship to TraitMech and METPO

This document investigates potential overlap between EcoMech and two related resources — TraitMech and METPO — and identifies opportunities for differentiation, cross-linking, and future integration.

---

## Resource Summaries

### METPO — Microbial Ecophysiology Traits and Phenotypes Ontology

- **Source**: Berkeley Bioinformatics Open-source Projects (BBOP); available on BioPortal and GitHub (`berkeleybop/metpo`)
- **Purpose**: A formal OBO Foundry ontology capturing the physiological traits and phenotypes of microorganisms, developed to enable systematic mining of organism descriptions from primary literature (particularly IJSEM)
- **Coverage**: Organism-level microbial characteristics — metabolic capabilities (e.g., aerobic/anaerobic respiration, fermentation pathways), growth conditions (temperature, pH, salinity tolerance), morphology, and ecophysiological roles
- **Anchoring**: Uses its own CURIE namespace (`https://w3id.org/metpo/`) with 7-digit local identifiers; imports and aligns with 24+ OBO ontologies including ENVO, GO, PATO, CHEBI, and RO
- **Use case**: Semantic integration of organism-level trait data from databases such as BactoTraits, BacDive, and Madin et al.; feeds into the KG-Microbe knowledge graph

### TraitMech — Microbial Ecophysiological Trait Knowledge Base

- **Source**: CultureBotAI (`culturebotai/TraitMech`); site at https://culturebotai.github.io/TraitMech/
- **Purpose**: A curated KB of microbial traits, seeded from METPO and curated incrementally; part of a broader "Mech" family of databases covering culture conditions, media, and community dynamics
- **Coverage**: 477 trait records across 9 categories:

  | Category | Records |
  |---|---|
  | Metabolism | 143 |
  | Environment | 121 |
  | Morphology | 88 |
  | Physiology | 45 |
  | Ecology | 26 |
  | Observation | 20 |
  | Genomics | 19 |
  | Upper | 8 |
  | Quantitative Property | 7 |

- **Schema**: LinkML-based (`TraitRecord` as root class) with `CausalGraph` / `CausalNode` / `CausalEdge` for mechanistic representation and `EvidenceItem` (reference + verbatim snippet) for literature support; curation tracked via `CurationEvent` with LLM-assist flags
- **Ontology xrefs**: METPO (primary identifier), GO, ENVO, PATO, CHEBI, NCBITaxon, RO, OBI
- **Canonical organisms**: Each trait can have `CanonicalExample` entries grounding it in a specific taxon (NCBITaxon CURIE)

---

## Scale and Scope Comparison

The most important distinction between EcoMech and these resources is **level of organization**:

| Dimension | METPO / TraitMech | EcoMech |
|---|---|---|
| Primary subject | Individual microorganism | Ecological process (ecosystem level) |
| Anchoring ontology | METPO namespace | ENVO ecosystem process branch (ENVO:02500000) |
| Organism scope | Bacteria and archaea | All organisms (microbes, plants, animals, fungi) |
| Abiotic context | Growth conditions for culturing | Ecosystem-scale abiotic drivers and indicators |
| Process description | "Organism X has trait Y" | "Process Z operates via mechanism M, driven by D, measured by I, managed by V" |
| Interventions | None | Restoration, management, policy interventions |
| Habitat context | Culture media / growth conditions | ENVO biomes and ecosystems |
| Scale | Organism / population | Ecosystem / landscape / global |

METPO and TraitMech answer: *What can microorganism X do?*
EcoMech answers: *How does ecological process Z work, what drives it, how do we measure it, and how do we manage it?*

---

## Areas of Genuine Overlap

Despite the scale difference, there are meaningful zones of shared conceptual territory:

### 1. Microbial mechanisms in biogeochemical cycles

EcoMech's `mechanisms[].biological_processes` (GO-term annotated) and `taxa_involved` entries describe what microorganisms do within an ecosystem process — which is precisely what TraitMech's Metabolism and Ecology trait categories represent at the organism level.

**Concrete examples:**

| EcoMech entry | Equivalent TraitMech/METPO concept |
|---|---|
| Nitrogen Cycling → Biological Nitrogen Fixation (mechanism) | TraitMech Metabolism: nitrogen fixation trait; CanonicalExample: *Rhizobium* spp. |
| Nitrogen Cycling → Nitrification (mechanism) | TraitMech Metabolism: ammonia oxidation trait; CanonicalExample: *Nitrosomonas* spp. |
| Nitrogen Cycling → Denitrification (mechanism) | TraitMech Metabolism: denitrification trait |
| Sulfur Cycling → Dissimilatory Sulfate Reduction | TraitMech Metabolism: sulfate reduction trait; CanonicalExample: *Desulfovibrio* spp. |
| Carbon Cycling → Ecosystem Respiration | TraitMech Physiology/Metabolism: aerobic/anaerobic respiration traits |

The overlap is **real but complementary**: EcoMech provides the ecosystem context and evidence for why these microbial activities matter at scale; TraitMech provides the organism-resolved trait inventory of which microbes carry out each activity.

### 2. Shared ontology vocabulary

Both resources use the same underlying ontologies, enabling direct cross-linking without translation:

- **GO** — biological process terms (used in EcoMech `biological_processes`, in TraitMech `xrefs`)
- **ENVO** — environmental conditions (used in EcoMech `abiotic_conditions` and `habitat_context`, in TraitMech `Environment` traits)
- **PATO** — quality/phenotype terms (used in EcoMech `indicator_term`, in TraitMech `xrefs`)
- **CHEBI** — chemical entities (used in EcoMech `chemical_entities`, in TraitMech `xrefs`)
- **NCBITaxon** — taxon identifiers (used in EcoMech `taxa_involved`, in TraitMech `CanonicalExample`)

### 3. Causal graph architecture

Both use directed causal graphs with typed edges as the primary mechanism representation:

| Feature | TraitMech | EcoMech |
|---|---|---|
| Node types | TRAIT, PATHWAY, ENVIRONMENTAL_FACTOR, CHEMICAL, GENE_OR_PROTEIN, STATE, CAPACITY | Free-text subjects/objects |
| Edge predicate | Typed (RO terms) | Typed enum (CAUSES, ENABLES, INHIBITS, etc.) |
| Evidence on edges | Required per edge | At mechanism level |
| Schema language | LinkML | LinkML |

EcoMech's causal edges are currently less formally typed than TraitMech's (subjects/objects are free text rather than grounded nodes). TraitMech's more structured `CausalNode` model could inform a future EcoMech schema revision.

### 4. Evidence model

Both use a reference + verbatim snippet pattern for literature evidence, with `EvidenceItem` as the shared conceptual unit. TraitMech's `EvidenceItem` has `reference`, `snippet`, and `notes`; EcoMech's has `reference`, `snippet`, `explanation`, `supports`, and `evidence_source`. EcoMech's model is richer (support polarity, study type classification), while TraitMech's is more lightweight.

---

## Key Differences and Where EcoMech Is Distinct

EcoMech covers territory that METPO and TraitMech explicitly do not:

1. **Multi-trophic process descriptions** — EcoMech mechanisms involve plants, animals, fungi, and microbes interacting within the same process (e.g., mycorrhizal P uptake involves both plant roots and AMF). TraitMech is microbe-centric.

2. **Ecosystem-scale drivers** — climate variables, land-use change, atmospheric deposition, and anthropogenic stressors as quantified drivers of process rates. TraitMech covers growth conditions at the culture level (temperature optima, pH tolerance).

3. **Quantitative indicators** — measurement protocols, sampling frequencies, and temporality of ecosystem-level observables (e.g., soil NO3- in mg/kg, N2O flux in μg m-2 h-1). Not represented in METPO/TraitMech.

4. **Management interventions** — restoration practices, conservation policy, and agricultural management with evidence from field studies and meta-analyses. No equivalent in METPO/TraitMech.

5. **ENVO ecosystem process anchoring** — every EcoMech entry is grounded in a term from the ENVO:02500000 hierarchy, enabling integration with Earth system ontologies (SWEET, ENVO), remote sensing products, and ecological monitoring databases. METPO/TraitMech are not anchored to ecosystem process ontologies.

6. **Non-microbial processes** — primary production by vascular plants, vertebrate trophic processes, pollination, seed dispersal, and disturbance/succession are outside the scope of METPO/TraitMech but within EcoMech's Phase 2 target list.

---

## Integration Opportunities

The complementarity of these resources suggests several concrete integration paths:

### Near-term: Cross-linking in EcoMech KB entries

EcoMech's `taxa_involved` entries could be extended to reference TraitMech trait IDs for the relevant microbial actors. For example, in `Nitrogen_Cycling.yaml`, the nitrification mechanism could xref the TraitMech record for "ammonia oxidation" trait. This would allow users to navigate from an ecosystem process to the organism-level trait inventory without duplicating curation.

**Proposed addition to schema:**
```yaml
taxa_involved:
  - taxon:
      id: NCBITaxon:1246
      label: Nitrosomonas
    role: NITRIFIER
    trait_xrefs:
      - id: METPO:0000XXX
        label: ammonia oxidation
```

### Medium-term: Unified graph export

Both EcoMech and TraitMech are designed to export to KGX/CX2 knowledge graph formats. A joint graph could link ENVO ecosystem process nodes (EcoMech) to METPO trait nodes (TraitMech) via NCBITaxon organism nodes, enabling queries like: *"Which organisms carry the traits required for nitrogen fixation, and in which ecosystem processes does this trait play a mechanistic role?"*

### Longer-term: Shared causal graph schema

EcoMech's current free-text causal edge subjects/objects could be upgraded to adopt TraitMech's grounded `CausalNode` model (with `node_type` and ontology `grounding`), enabling machine-readable causal inference across both resources and direct alignment with RO predicates.

---

## Summary

METPO and TraitMech are **complementary to EcoMech, not redundant with it.** They operate at the organism/trait level while EcoMech operates at the ecosystem/process level. The main zone of genuine overlap is in the microbial mechanism descriptions of biogeochemical cycle entries (nitrogen, sulfur, carbon cycling), where EcoMech's `taxa_involved` and `biological_processes` describe the same actors as TraitMech's Metabolism traits — but in a different ecological context and at a different scale.

The shared use of LinkML schemas, OBO ontology vocabulary (GO, ENVO, PATO, CHEBI, NCBITaxon), and literature evidence models makes formal cross-linking technically straightforward and scientifically valuable. The most impactful near-term action would be to add `trait_xrefs` to EcoMech's `taxa_involved` entries for microbe-driven mechanisms, establishing EcoMech as the ecosystem-level layer of a multi-scale knowledge graph in which METPO/TraitMech provide organism-level resolution.
