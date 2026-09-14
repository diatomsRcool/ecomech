# ENVO Habitat Terms — Curation Quick Reference

All IDs verified against the ENVO sqlite db (`~/.data/oaklib/envo.db`).
Use `just validate-terms-file` to confirm any ID before committing.

## Existing KB terms (already in use)

| ENVO ID | Verified label | Notes |
|---------|---------------|-------|
| ENVO:01000202 | temperate broadleaf forest biome | Preferred for temperate deciduous forest |
| ENVO:01000212 | temperate mixed forest biome | Conifer-broadleaf mix |
| ENVO:01000245 | cropland biome | Agricultural systems |
| ENVO:00000043 | wetland area | General wetland; prefer more specific terms below |
| ENVO:00000873 | freshwater biome | Lakes, rivers, ponds |
| ENVO:01000854 | tropical marine coral reef biome | Coral reef systems |

## Terrestrial biomes to add

| Biome type | ENVO ID | Verified label |
|------------|---------|---------------|
| Tropical rainforest | ENVO:01000228 | tropical moist broadleaf forest biome |
| Tropical dry forest | ENVO:01000227 | tropical dry broadleaf forest biome |
| Tropical savanna | ENVO:01000188 | tropical savanna biome |
| Tropical grassland | ENVO:01000192 | tropical grassland biome |
| Boreal / taiga forest | ENVO:01000250 | subpolar coniferous forest biome |
| Temperate grassland / prairie | ENVO:01000193 | temperate grassland biome |
| Tundra (arctic) | ENVO:01000180 | tundra biome |
| Alpine tundra | ENVO:01001505 | alpine tundra biome |
| Mediterranean shrubland | ENVO:01000217 | mediterranean shrubland biome |
| Desert / xeric shrubland | ENVO:01000218 | xeric shrubland biome |
| Mangrove | ENVO:01000181 | mangrove biome |
| Peatland / bog | ENVO:00000044 | peatland |

## Marine and aquatic biomes to add

| Biome type | ENVO ID | Verified label |
|------------|---------|---------------|
| Open ocean / pelagic | ENVO:01000023 | marine pelagic biome |
| Ocean (broad) | ENVO:01000048 | ocean biome |
| Kelp forest | ENVO:01000058 | kelp forest |
| Estuary | ENVO:00000045 | estuary |
| Coastal wetland | ENVO:00000230 | coastal wetland ecosystem |

## Terms from the plan that were WRONG — do not use

The following IDs appeared in the original enhancement plan but resolve to
incorrect or obsolete terms. Use the verified IDs above instead.

| Plan ID | Actual label (wrong) | Use instead |
|---------|---------------------|-------------|
| ENVO:01000179 | desert biome | ENVO:01000218 (xeric shrubland biome) |
| ENVO:01000180 | tundra biome | ✓ correct for arctic tundra |
| ENVO:01000197 | broadleaf forest biome | ENVO:01000228 (tropical moist broadleaf) |
| ENVO:01000222 | subtropical woodland biome | ENVO:01000193 (temperate grassland biome) |
| ENVO:01000248 | dense settlement biome | ENVO:01000218 (xeric shrubland biome) |
| ENVO:01000349 | root matter | ENVO:01001505 (alpine tundra biome) |
| ENVO:01000208 | mediterranean woodland biome | ENVO:00000044 (peatland) |
| ENVO:00000276 | drumlin | ENVO:00000045 (estuary) |
