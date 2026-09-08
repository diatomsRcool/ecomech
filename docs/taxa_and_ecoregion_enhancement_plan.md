# Taxa Specificity & Ecoregion Coverage Enhancement Plan

## Baseline Audit

Current state of the 24-entry KB (as of September 2026):

### Taxonomic resolution

| Rank | Count | Example IDs |
|------|-------|-------------|
| Domain / Kingdom | 6 | Bacteria, Archaea, Fungi, Viridiplantae, Eukaryota |
| Phylum | 8 | Arthropoda, Annelida, Basidiomycota, Embryophyta, Bacillariophyta, Cyanobacteria, Glomeromycota, Dinophyceae |
| Class / Order | 7 | Mammalia, Insecta, Aves, Actinopterygii, Scleractinia |
| Genus | 11 | Nitrosomonas, Desulfovibrio, Geobacter, Pinus, Bombus, … |
| Species | 3 | *Rhizobium leguminosarum*, *Apis mellifera*, *Pseudomonas aeruginosa* |

**~60% of the 32 unique taxa are at phylum level or above.** The three species-level
entries are all in well-studied temperate or model-organism contexts.

### Ecoregion / habitat coverage

Only **6 unique ENVO habitat terms** appear across all 24 processes:

| ENVO ID | Label | Processes |
|---------|-------|-----------|
| ENVO:01000245 | temperate mixed forest biome | 10 |
| ENVO:00000446 | temperate broadleaf mixed forest biome | 14 |
| ENVO:00000043 | wetland | 5 |
| ENVO:00000015 | cropland ecosystem | 3 |
| ENVO:00000873 | freshwater lake | 3 |
| ENVO:00000447 | tropical marine coral reef biome | 1 |

**16 major biome types are completely absent:**
tropical rainforest, tropical dry forest, tropical savanna/grassland, boreal/taiga forest,
arctic/alpine tundra, desert/dryland, Mediterranean shrubland, temperate grassland/prairie,
peatland/bog, mangrove, kelp forest, open ocean/pelagic, deep sea, montane/alpine,
tropical montane forest, estuaries/coastal wetland.

Two marine processes (Marine Primary Production, Marine Benthic Primary Production) have
**zero habitat context entries**.

---

## Root Causes

1. **Schema permissiveness** — the schema accepts any NCBITaxon CURIE; no minimum
   rank requirement nudges curators toward specificity.
2. **Literature bias** — ecological research is heavily biased toward temperate systems;
   curators naturally reach for the most-cited papers, which are often temperate.
3. **No curation target for diversity** — the current compliance checker scores on
   evidence presence but not on taxonomic resolution or biome breadth.
4. **Mechanism structure is habitat-blind** — only the top-level `habitat_context` slot
   exists; individual mechanisms cannot be tagged to specific biomes, so biome-specific
   evidence is hard to attach.

---

## Part 1 — Taxonomic Specificity Upgrade

### Target: replace all taxa above genus level

**Priority replacements (grouped by current broad taxon):**

#### `NCBITaxon:2` Bacteria / `NCBITaxon:2157` Archaea (appear 15 times combined)

Replace with functional-group genera backed by primary literature:

| Process | Role | Replace with |
|---------|------|-------------|
| Litter Decomposition | DECOMPOSER | *Streptomyces* (NCBITaxon:1883), *Trichoderma* (NCBITaxon:5543) |
| Methane Cycling | DECOMPOSER (methanogens) | *Methanobacterium* (NCBITaxon:2160), *Methanosarcina* (NCBITaxon:2207) |
| Methane Cycling | DECOMPOSER (methanotrophs) | *Methylococcus* (NCBITaxon:415), *Methylocystis* (NCBITaxon:68) |
| Sulfur Cycling | DECOMPOSER | *Desulfovibrio* (keep), *Sulfurimonas* (NCBITaxon:222962) |
| Iron Cycling | OTHER | *Shewanella* (NCBITaxon:22), *Acidithiobacillus ferrooxidans* (NCBITaxon:920) |
| Redox Dynamics | DECOMPOSER | *Geobacter* (keep), *Anaeromyxobacter* (NCBITaxon:161492) |
| Nitrogen Cycling | DENITRIFIER | *Paracoccus denitrificans* (NCBITaxon:266), not just *P. aeruginosa* |
| Carbon Cycling | DECOMPOSER | *Streptomyces*, *Bacillus subtilis* (NCBITaxon:1423) |
| Phosphorus Cycling | DECOMPOSER | *Bacillus* (keep), *Aspergillus niger* (NCBITaxon:5061) |

#### `NCBITaxon:4751` Fungi (appears 6 times)

Replace with functional guild genera:

| Process | Replace with |
|---------|-------------|
| Litter Decomposition | *Trichoderma* (NCBITaxon:5543), *Aspergillus* (NCBITaxon:5052) |
| Carbon Cycling | *Penicillium* (NCBITaxon:5073), *Aspergillus* |
| Mycorrhizal Association | *Rhizophagus irregularis* (NCBITaxon:588596), *Pisolithus* (NCBITaxon:37132) |
| Redox Dynamics | *Aspergillus* |
| Nitrogen Cycling | *Mortierella* (NCBITaxon:74868) |
| Wildfire Succession | *Pyronema* (NCBITaxon:5204-class) → *Pholiota* (NCBITaxon:5341) |

#### `NCBITaxon:33090` Viridiplantae / `NCBITaxon:3193` Embryophyta (appears 9 times)

These are acceptable as placeholders in multi-biome processes but should be
supplemented with biome-specific taxa (see Part 2). Minimum target: class level.

| Process | Add (biome-specific, see Part 2) |
|---------|----------------------------------|
| Terrestrial Primary Production | *Quercus* (NCBITaxon:3511), *Zea mays* (NCBITaxon:4577), *Sphagnum* (NCBITaxon:3217) |
| Carbon Sequestration | *Picea* (NCBITaxon:3337-related), *Sphagnum* (NCBITaxon:3217) |
| Gap Dynamics | *Cecropia* (NCBITaxon:3490) for tropical variant |

#### `NCBITaxon:40674` Mammalia / `NCBITaxon:6960` Insecta / `NCBITaxon:8782` Aves (appear 10 times)

| Process | Role | Replace with |
|---------|------|-------------|
| Herbivory | CONSUMER | *Bison* (NCBITaxon:9901), *Cervus* (NCBITaxon:9870), *Acrididae* (NCBITaxon:7002) |
| Predation | PREDATOR | *Canis lupus* (NCBITaxon:9612), *Panthera leo* (NCBITaxon:30657) |
| Predation | PREY | *Odocoileus* (NCBITaxon:9877), *Connochaetes* (NCBITaxon:9895) |
| Seed Dispersal | SEED_DISPERSER | *Turdus* (thrushes, NCBITaxon:9302), *Alouatta* (howler monkeys, NCBITaxon:9011) |
| Pollination | POLLINATOR | *Bombus* (keep), add *Xylocopa* (carpenter bees, NCBITaxon:6500), *Hyles* (hawk moths) |
| Detritivory | DETRITIVORE | *Lumbricus terrestris* (NCBITaxon:6391), *Porcellio scaber* (NCBITaxon:6549) |

#### `NCBITaxon:6340` Annelida / `NCBITaxon:6656` Arthropoda (appear 5 times in Detritivory)

| Current | Replace with |
|---------|-------------|
| Annelida | *Lumbricus terrestris* (NCBITaxon:6391), *Eisenia fetida* (NCBITaxon:6396) |
| Arthropoda | *Porcellio scaber* (isopod, NCBITaxon:6549), *Tomocerus* (collembola, NCBITaxon:37514) |

#### Bacillariophyta / Cyanobacteria (marine primary production)

These are at the right level for broad processes but need biome-specific genera:

| Process | Add |
|---------|-----|
| Marine Primary Production | *Thalassiosira* (NCBITaxon:35128), *Prochlorococcus* (NCBITaxon:1218), *Emiliania huxleyi* (NCBITaxon:2903) |
| Marine Benthic Production | *Navicula* (NCBITaxon:35128-related), *Oscillatoria* (NCBITaxon:1166) |

### Schema change to enforce minimum rank

Add a compliance warning (not a validation error) when taxon IDs resolve to ranks above
genus. Implement in `src/ecomech/analysis/compliance.py` as a soft check:

```python
# Taxon IDs at rank ≥ phylum that should trigger a curation warning
_BROAD_TAXON_IDS = {
    "NCBITaxon:2",     # Bacteria
    "NCBITaxon:2157",  # Archaea
    "NCBITaxon:2759",  # Eukaryota
    "NCBITaxon:4751",  # Fungi
    "NCBITaxon:33090", # Viridiplantae
    "NCBITaxon:3193",  # Embryophyta
    "NCBITaxon:6656",  # Arthropoda
    "NCBITaxon:6340",  # Annelida
    "NCBITaxon:40674", # Mammalia
    "NCBITaxon:6960",  # Insecta
    "NCBITaxon:8782",  # Aves
    "NCBITaxon:7898",  # Actinopterygii
    "NCBITaxon:2759",  # Eukaryota
}
```

---

## Part 2 — Biome / Ecoregion Coverage Expansion

### Biome ENVO terms to use

Curators should use these ENVO terms when adding habitat context. Validate with
`just validate-terms-file` before committing.

| Biome | ENVO ID (verify before use) |
|-------|---------------------------|
| Tropical rainforest | ENVO:01000179 |
| Tropical dry forest | ENVO:01000197 |
| Tropical savanna/grassland | ENVO:01000180 |
| Boreal / taiga forest | ENVO:01000250 |
| Temperate grassland / prairie | ENVO:01000222 |
| Arctic / alpine tundra | ENVO:01000349 |
| Mediterranean shrubland | ENVO:01000217 |
| Desert / xeric shrubland | ENVO:01000248 |
| Mangrove | ENVO:01000181 |
| Peatland / mire / bog | ENVO:00000043-subtype or ENVO:01000208 |
| Kelp forest | ENVO:01000048-subtype |
| Open ocean / pelagic | ENVO:01000048 |
| Montane / alpine grassland | ENVO:01000222-subtype |
| Estuary / coastal wetland | ENVO:00000276 |

### Priority biome additions by process

#### Tier 1 — Immediate (zero habitats or only 1 temperate habitat)

| Process | Add habitats | Key taxon additions | Scientific rationale |
|---------|-------------|---------------------|----------------------|
| Marine Primary Production | open ocean, coastal upwelling | *Prochlorococcus*, *Synechococcus* (oligotrophic); *Thalassiosira*, *Chaetoceros* (eutrophic) | Tropical gyres vs polar blooms are mechanistically distinct |
| Marine Benthic Production | benthic marine, mangrove | *Navicula*, *Oscillatoria* (benthic); *Avicennia*-associated taxa | Benthic PAR and sediment nutrients vary enormously |
| Flood Pulse | tropical floodplain, várzea | *Colossoma macropomum* (tambaqui), *Arapaima* | Flood pulse concept originated in Amazon, not temperate |
| Wildfire Succession | tropical savanna, boreal | *Pinus* (keep for boreal), *Usnea*, post-fire *Ceanothus* | Fire regimes differ fundamentally: crown fire vs surface fire |
| Gap Dynamics | tropical rainforest | *Cecropia*, *Heliconia* (pioneers), *Dipteryx* (canopy) | Tropical gap dynamics (high diversity, fast closure) differ from temperate |
| Pollination | tropical rainforest, arid | Orchid bees (*Eulaema*), hawk moths (*Manduca*), bats (*Leptonycteris*) | Specialist pollination syndromes dominate in tropics and deserts |
| Seed Dispersal | tropical, savanna | *Alouatta*, *Tapirus*, *Elephas maximus* (megafauna) | Megafaunal dispersal critical in tropics; absent in temperate entries |
| Water Filtration | coastal/estuary, freshwater streams | *Crassostrea* (oysters), *Mytilus*, freshwater mussels | Marine filtration by bivalves is a distinct and better-studied system |

#### Tier 2 — High value (strong biogeochemical differences by biome)

| Process | Missing biomes | Key additions | Why it matters |
|---------|---------------|---------------|----------------|
| Litter Decomposition | tropical rainforest, arctic tundra | *Termitomyces* (termite symbiont) for tropical; *Enchytraeidae* for arctic | Decomp rates span 10×; tropical dominated by termites and fungi, arctic by enchytraeids |
| Nitrogen Cycling | tropical forest, arctic tundra, marine | *Nitrososphaera* (AOA, soil), *Candidatus Scalindua* (marine anammox) | Tropical N cycling is mineralization-dominated; arctic is severely N-limited |
| Carbon Sequestration | peatland/bog, boreal forest | *Sphagnum* (NCBITaxon:3217), *Picea mariana* (NCBITaxon:99598) | Northern peatlands hold ~30% of terrestrial C; Sphagnum is the key taxon |
| Methane Cycling | peatland, rice paddy, permafrost thaw | *Methanosaeta* (NCBITaxon:2223), *Methanobrevibacter* (NCBITaxon:2172) | Rice paddies and permafrost are major anthropogenic CH4 sources |
| Redox Dynamics | mangrove, marine sediment | *Desulfobacter* (NCBITaxon:29500), *Beggiatoa* (NCBITaxon:1007) | Mangrove sediments have steep redox gradients; Beggiatoa is diagnostic |
| Iron Cycling | tropical laterite soil, deep sea hydrothermal | *Acidithiobacillus ferrooxidans* (acid mine), *Zetaproteobacteria* (marine) | Deep-sea vent iron cycling involves novel taxa absent from current entries |
| Sulfur Cycling | hydrothermal vent, salt marsh | *Allochromatium vinosum* (NCBITaxon:572), *Candidatus Thioglobus* | Purple sulfur bacteria and salt marsh sulfur cycling are textbook examples |

#### Tier 3 — Completeness

| Process | Missing biomes to add |
|---------|-----------------------|
| Herbivory | tropical savanna (termites as dominant herbivores), boreal (moose-spruce), marine (urchin-kelp) |
| Predation | marine (orca-seal), tropical (Panthera-ungulate), boreal (wolf-moose) |
| Mycorrhizal Association | boreal (ectomycorrhizal dominance: *Amanita*, *Suillus*), tropical (arbuscular dominates) |
| Phosphorus Cycling | tropical weathering-limited soils, marine P recycling |
| Carbon Cycling | tropical peatland, boreal forest, permafrost thaw C release |

---

## Part 3 — Tooling & Workflow Enhancements

### 3a. Taxon broadness check in compliance.py

Add a check that emits a curation warning for any `taxa_involved` entry using
a known above-genus taxon ID. Include the count in the compliance report and
`just coverage` dashboard.

### 3b. Biome coverage matrix in coverage dashboard

Extend `src/ecomech/analysis/coverage.py` to generate a biome × process coverage
matrix showing which processes have evidence from which biome types. Color-code:
green = ≥2 evidence items from that biome, yellow = 1, grey = absent.

Biome classification uses the ENVO term's habitat_context entries.

### 3c. GBIF taxon-by-role lookup

Extend `src/ecomech/ingest/gbif.py` to support a `taxa-for-role` subcommand:

```bash
just gbif-taxa-for-role "nitrogen fixation" --rank genus
# Returns: Rhizobium, Sinorhizobium, Mesorhizobium, Bradyrhizobium, …
```

This queries GBIF's species API filtered by trait keywords and returns verified
NCBITaxon CURIEs via nubKey resolution.

### 3d. Updated /curate skill

Update `.claude/skills/curate.md` to require:
- At minimum **3 taxa at genus level or below** per process
- At least **2 distinct biome types** in `habitat_context`
- A note to check the taxon broadness table in this document before committing

### 3e. ENVO habitat term reference

Create `docs/envo_habitat_terms.md` as a curation quick-reference listing the
ENVO IDs for all major biome types (verified by `just validate-terms-file`).

---

## Part 4 — Implementation Order

| Phase | Action | Effort | Entries affected |
|-------|--------|--------|-----------------|
| **4a** | Validate ENVO habitat term IDs from the table above; create `docs/envo_habitat_terms.md` | Low | All future entries |
| **4b** | Add habitat_context to Marine Primary Production and Marine Benthic Production (currently zero) | Low | 2 |
| **4c** | Add broad-taxon warning to `compliance.py`; regenerate `just coverage` | Low | All |
| **4d** | Curate Tier 1 habitat + taxon additions (Flood Pulse, Wildfire, Gap Dynamics, Pollination, Seed Dispersal, Water Filtration) | Medium | 6 |
| **4e** | Replace all Bacteria/Archaea/Fungi instances with genus-level taxa (Methane, Sulfur, Iron, Redox, Litter Decomposition) | Medium | 7 |
| **4f** | Add Tier 2 biome variants to biogeochemical cycles (N, C, P, CH4, Redox) | High | 5 |
| **4g** | Replace Mammalia/Insecta/Aves with genus/species in Herbivory, Predation, Seed Dispersal, Detritivory | Medium | 4 |
| **4h** | Add biome coverage matrix to `just coverage` dashboard | Medium | tooling |
| **4i** | Update /curate skill with minimum taxon rank and biome diversity requirements | Low | skill |

---

## Expected Outcomes

After full implementation:

| Metric | Current | Target |
|--------|---------|--------|
| Unique taxa | 32 | ~100 |
| Taxa at species/genus level | 40% | ≥80% |
| Unique habitat terms | 6 | ≥20 |
| Biome types represented | 2 (temperate forest + freshwater) | ≥10 |
| Processes with ≥3 biome contexts | 0 | ≥15 |
| Processes with ≥5 taxa | 3 | ≥15 |

---

## Appendix: Verified Genus-Level Taxa for Common Functional Roles

A quick-reference for curators (all NCBITaxon IDs should be verified with
`just validate-terms-file` before use):

| Role | Habitat | Genus/Species | NCBITaxon |
|------|---------|---------------|-----------|
| Methanogen | Wetland, peatland | *Methanobacterium* | 2160 |
| Methanogen | Freshwater sediment | *Methanosarcina* | 2207 |
| Methanotroph | Soil, freshwater | *Methylococcus* | 415 |
| Methanotroph | Wetland | *Methylocystis* | 68 |
| Sulfate reducer | Anoxic sediment | *Desulfovibrio* | 872 |
| Sulfur oxidizer | Aerobic/anoxic | *Sulfurimonas* | 222962 |
| Iron reducer | Anoxic sediment | *Geobacter* | 28231 |
| Iron reducer | Marine | *Shewanella* | 22 |
| Iron oxidizer (acid) | Acid mine drainage | *Acidithiobacillus ferrooxidans* | 920 |
| Nitrifier (AOB) | Soil, water | *Nitrosomonas* | 1246 |
| Nitrifier (AOA) | Soil | *Nitrososphaera* | 1511845 |
| Nitrifier (NOB) | Soil, water | *Nitrobacter* | 1742 |
| Denitrifier | Soil | *Paracoccus denitrificans* | 266 |
| N₂ fixer (free-living) | Soil | *Azotobacter* | 352 |
| Anammox | Marine, wastewater | *Candidatus Scalindua* | 333955 |
| Decomposer (fungi) | Forest soil | *Trichoderma* | 5543 |
| Decomposer (fungi) | Forest soil | *Aspergillus* | 5052 |
| Post-fire fungus | Boreal soil | *Pholiota* | 5341 |
| AM mycorrhiza | Most terrestrial | *Rhizophagus irregularis* | 588596 |
| EM mycorrhiza | Boreal/temperate | *Suillus* | 5478 |
| Earthworm | Temperate soil | *Lumbricus terrestris* | 6391 |
| Isopod | Forest litter | *Porcellio scaber* | 6549 |
| Phytoplankton | Open ocean | *Prochlorococcus* | 1218 |
| Phytoplankton | Upwelling | *Thalassiosira* | 35128 |
| Coccolithophore | Open ocean | *Emiliania huxleyi* | 2903 |
| Peatland moss | Boreal/arctic | *Sphagnum* | 3217 |
| Tropical pioneer tree | Rainforest gap | *Cecropia* | 3490 |
| Boreal conifer | Taiga | *Picea mariana* | 99598 |
| Savanna apex predator | Savanna | *Panthera leo* | 30657 |
| Boreal apex predator | Boreal/tundra | *Canis lupus* | 9612 |
| Megafaunal seed disperser | Tropical | *Tapirus* | 9722 |
| Tropical pollinator | Rainforest | *Eulaema* (orchid bee) | 213335 |
| Desert pollinator | Arid | *Xylocopa* (carpenter bee) | 6500 |
