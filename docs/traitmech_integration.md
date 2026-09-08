# EcoMech × TraitMech: Overlap Analysis & Linkage Proposals

## The Core Relationship

[TraitMech](https://github.com/CultureBotAI/TraitMech) is a curated knowledge base of
microbial ecophysiological traits seeded from METPO (Microbial Ecophysiological Traits
Ontology). EcoMech and TraitMech are **complementary vertical layers** of the same
biological reality:

| Dimension | TraitMech | EcoMech |
|-----------|-----------|---------|
| Primary unit | Organism-level ecophysiological trait | Ecosystem-level process |
| Ontology anchor | METPO (trait ontology) | ENVO:02500000 (ecosystem process) |
| Organism resolution | UniProtKB protein accessions + NCBITaxon | NCBITaxon with functional role |
| Mechanism depth | Molecular (gene/protein nodes, UniProt) | Ecological (GO terms, taxa, chemicals) |
| Scale | Organism → population | Community → global |
| Microbial focus | Strongly yes (477 records, all microbial) | Mixed (microbial + macro-ecological) |
| Evidence model | DOI + snippet + notes | PMID + snippet + `supports` enum + `evidence_source` |

The nitrogen-fixing symbiosis example shows this clearly: TraitMech's
`nitrogen_fixing_symbiosis.yaml` describes the *Sinorhizobium meliloti* NifH protein
mechanism at the molecular level; EcoMech's `Root_Nodule_Symbiosis.yaml` and
`Nitrogen_Cycling.yaml` describe the ecosystem-level consequences (soil N availability,
plant productivity, restoration interventions). They describe the same biology at
different scales.

## Overlap Map

### Direct process ↔ trait pairs

| EcoMech Process | TraitMech Traits |
|-----------------|-----------------|
| Nitrogen_Cycling, Root_Nodule_Symbiosis | `nitrogen_fixing_symbiosis`, `nitrogen_fixation`, `denitrification`, `dissimilatory_nitrate_reduction_to_ammonium` |
| Litter_Decomposition, Carbon_Cycling | `saprotrophy`, `carbon_fixation`, `uses_as_carbon_source` |
| Sulfur_Cycling | `dissimilatory_sulfate_reduction`, `sulfur_oxidation` |
| Iron_Cycling, Redox_Dynamics | `dissimilatory_iron_reduction`, `iron_oxidation`, `dissimilatory_manganese_reduction` |
| Methane_Cycling | `methanogenesis`, `anaerobic_oxidation_of_methane` |
| Marine_Primary_Production, Terrestrial_Primary_Production | `carbon_fixation`, `photosynthesis`, `calvin_benson_bassham_cycle` |
| Mycorrhizal_Association, Coral_Zooxanthellae_Symbiosis | `mutualism`, `endosymbiosis` |
| Root_Nodule_Symbiosis | `nitrogen_fixing_symbiosis` (essentially the same entity at different scales) |

### Shared ontology nodes (natural bridge points)

- **NCBITaxon** — EcoMech `taxa_involved`, TraitMech `canonical_examples` and `protein_examples.taxon_id`
- **GO** — EcoMech `biological_processes`, TraitMech `BIOLOGICAL_PROCESS` node grounding
- **CHEBI** — EcoMech `chemical_entities`, TraitMech chemical node grounding
- **ENVO** — EcoMech `habitat_context` + `driver_term`, TraitMech environment trait `xrefs`

## Proposed Linkage Mechanisms

### 1. Mapping tables (zero schema changes — do this first)

**`mappings/traitmech_xref.tsv`** — process ↔ trait pairs:

```tsv
ecomech_id	ecomech_name	traitmech_id	traitmech_label	link_type	notes
ECOCORE:00000186	litter decomposition	traitmech:000055	saprotrophy	process_enabled_by_trait	Saprotrophs execute decomposition
ENVO:01001813	nitrogen cycling	traitmech:000044	nitrogen_fixing_symbiosis	process_includes_trait	Symbiotic N fixation is a mechanism within N cycling
ENVO:01001813	nitrogen cycling	traitmech:000170	denitrification	process_includes_trait	Denitrification is a mechanism within N cycling
ECOCORE:00000183	terrestrial primary production	traitmech:000XXX	carbon_fixation	process_enabled_by_trait	Carbon fixation is the molecular mechanism of NPP
```

`link_type` values:
- `process_includes_trait` — the trait is a mechanism component within the process
- `process_enabled_by_trait` — the trait is required for the process to occur
- `process_produces_trait_context` — the process creates the environmental conditions
  under which the trait is expressed

**`mappings/taxon_role_to_traitmech.tsv`** — EcoMech TaxonRoleEnum → TraitMech:

```tsv
taxon_role	traitmech_id	traitmech_label
NITROGEN_FIXER	traitmech:000044	nitrogen_fixing_symbiosis
NITROGEN_FIXER	traitmech:000170	nitrogen_fixation
DENITRIFIER	traitmech:000XXX	denitrification
DECOMPOSER	traitmech:000055	saprotrophy
NITRIFIER	traitmech:000XXX	nitrification
```

### 2. Add `traitmech_xref` to `TaxonDescriptor` (schema change)

When a taxon is listed in a mechanism with a functional role, optionally link to the
TraitMech record that defines that role:

```yaml
# In kb/processes/Root_Nodule_Symbiosis.yaml
mechanisms:
  - name: Biological Nitrogen Fixation
    taxa_involved:
      - taxon:
          id: NCBITaxon:382
          label: Sinorhizobium meliloti
        role: NITROGEN_FIXER
        traitmech_xref: traitmech:000044   # ← new optional slot
```

Schema addition in `src/ecomech/schema/ecomech.yaml`:

```yaml
# In TaxonDescriptor class
traitmech_xref:
  range: CurieType
  pattern: "^traitmech:\\d+$"
  description: >
    Cross-reference to the TraitMech trait record that defines the
    functional trait this taxon is exhibiting in this mechanism.
    Links organism-level protein mechanism to ecosystem-level process.
```

This is the highest-value linkage: it ties specific taxa in specific processes to their
protein-level mechanism in TraitMech, enabling traversal from UniProt → NCBITaxon →
EcoMech mechanism → ecosystem process.

### 3. KGX merge bridge (`src/ecomech/export/kgx_bridge.py`)

Both projects use biolink predicates. The KGX outputs can be merged via shared nodes:

- Shared nodes auto-merge by CURIE identity: NCBITaxon, GO, and CHEBI CURIEs that appear
  in both graphs collapse to the same node in the merged graph.
- A bridge script reads the mapping table and emits explicit cross-graph edges:

```
traitmech:000044 --biolink:related_to--> ENVO:01001813   (N cycling process)
traitmech:000055 --biolink:enables--> ecomech:Litter_Decomposition:enzyme_hydrolysis
```

A merged EcoMech + TraitMech KGX graph is loadable into Neo4j or Cytoscape for
cross-scale queries.

### 4. `conforms_to` referencing TraitMech causal graphs (convention, no schema change)

EcoMech's existing `conforms_to` slot can informally reference TraitMech causal graphs:

```yaml
mechanisms:
  - name: Enzymatic cellulose degradation
    conforms_to:
      - Decomposition_Cascade#Enzyme Hydrolysis
      - traitmech:saprotrophy#saprotrophy_causal_graph   # informal cross-reference
```

No validation is enforced, but the relationship is surfaced in YAML and HTML renders.

### 5. Reciprocal `xrefs` in TraitMech (PR to TraitMech repo)

TraitMech ecology and metabolism traits that correspond to EcoMech processes should add
`xrefs` entries pointing back to EcoMech CURIEs. This is a contribution to the TraitMech
repository rather than EcoMech:

```yaml
# In traitmech/data/traits/ecology/nitrogen_fixing_symbiosis.yaml
xrefs:
  - ECOCORE:00000189      # root nodule symbiosis (ECOCORE)
  - ecomech:Root_Nodule_Symbiosis
```

## Recommended Implementation Order

| Priority | Action | Effort | Schema change? |
|----------|--------|--------|---------------|
| 1 | Create `mappings/traitmech_xref.tsv` and `mappings/taxon_role_to_traitmech.tsv` | Low | No |
| 2 | Add `traitmech_xref` slot to `TaxonDescriptor`; backfill 5–6 entries | Medium | Yes |
| 3 | Build `src/ecomech/export/kgx_bridge.py` to merge KGX outputs | Medium | No |
| 4 | Open PRs to TraitMech adding EcoMech `xrefs` on ecology/metabolism records | Low | No (TraitMech side) |

## What This Enables

A merged EcoMech + TraitMech graph supports queries like:

- *"Which organisms carry out nitrogen fixation, what proteins are responsible (UniProt),
  and what ecosystem-level processes do they participate in?"*
- *"What microbial traits drive litter decomposition, and what are the restoration
  interventions when decomposition is impaired?"*
- *"Which ecosystem processes depend on traits expressed only under microaerobic conditions
  (from TraitMech's environment records)?"*

This is the microbial ecology layer of a unified ecological knowledge graph — analogous
to how the Monarch KG connects gene → phenotype → disease, but for
**microbe trait → ecosystem process → management intervention**.
