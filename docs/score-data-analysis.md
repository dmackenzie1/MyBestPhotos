# Score Data Analysis — Real Dataset Statistics

Generated from live database inspection of 17,086 photos.

## Dataset Overview

| Metric | Value |
|--------|-------|
| Total files | 17,086 |
| Date range | 2001-08-09 to 2026-04-23 |
| Width range | 89 – 8,000 px (median: 2,592) |
| Height range | 89 – 12,976 px (median: 2,448) |
| Q25 width | 1,600 px |
| Q75 width | 4,080 px |

## Aspect Ratio Distribution

Dominant aspect ratios in the dataset:

| Aspect Ratio | Count | % of Total | Common Names |
|--------------|-------|------------|--------------|
| 1.33 (4:3) | 10,050 | 58.8% | Standard camera, 6x8 print match |
| 0.75 (3:4) | 3,155 | 18.5% | Portrait orientation, 6x8 print match |
| 1.78 (16:9) | 868 | 5.1% | Widescreen video/crop |
| 2.22 (9:4) | 617 | 3.6% | Ultra-wide panorama |
| 1.49 (~3:2) | 377 | 2.2% | Full-frame camera native |
| 0.56 (~9:16) | 369 | 2.2% | Tall portrait video |
| 2.00 (2:1) | 347 | 2.0% | 10x5, 12x6 print match |
| Others (<1%) | ~1,303 | 7.6% | Various |

**Key insight for print scoring:** 77.3% of photos are 4:3 (landscape or portrait), which matches the 6x8 print ratio exactly. The 12x18 print (1.5:1) only matches ~2.2% of photos natively. Print scores should heavily penalize aspect-ratio mismatch for non-4:3 images.

## Camera Brand Distribution

| Make | Count | % of Total | Category |
|------|-------|------------|----------|
| Samsung / SAMSUNG | 5,675 | 33.2% | Phone |
| LG Electronics / LGE | 3,412 | 20.0% | Phone |
| Canon | 1,956 | 11.4% | DSLR/mirrorless + point-and-shoot |
| Panasonic | 1,512 | 8.8% | Compact/bridge camera |
| Apple | 1,267 | 7.4% | Phone (iPhone) |
| TCL | 1,160 | 6.8% | Phone |
| (none / missing EXIF) | 663 | 3.9% | Unknown |
| NIKON CORPORATION / NIKON | 517 | 3.0% | DSLR/mirrorless |
| EASTMAN KODAK COMPANY | 114 | 0.7% | Compact camera |
| Other (<0.5%) | ~280 | 1.6% | Various |

**Key insight:** Phones dominate (53.2%), followed by Canon DSLRs/compacts (11.4%). Any scoring bias toward "DSLR" brands should be removed — the dataset is phone-heavy and scores should reflect that reality, not assume a professional-camera baseline.

## Score Distributions (All 17,086 files populated, zero NULLs)

### Technical Scores

| Field | Min | P25 | Median | P75 | Max | Stddev | Notes |
|-------|-----|-----|--------|-----|-----|--------|-------|
| blur_score | 0.0000 | 0.1549 | 0.8092 | 0.9939 | 1.0000 | 0.4024 | Good spread; bimodal (in-focus vs out-of-focus) |
| brightness_score | 0.0000 | 0.1421 | 0.3675 | 0.5349 | 0.9996 | 0.2484 | Skewed low; most photos are darker than optimal 0.65 target |
| contrast_score | 0.0000 | 0.2883 | 0.3920 | 0.4835 | 1.0000 | 0.1540 | Moderate spread; low-contrast photos are common |
| entropy_score | 0.0000 | 0.8845 | 0.9284 | 0.9520 | 0.9959 | 0.0997 | **Compressed** — most natural photos have similar entropy; not useful for discrimination |
| noise_score | 0.0000 | 0.3864 | 0.5863 | 0.7410 | 1.0000 | 0.2433 | Good spread; phone cameras show higher noise than DSLRs |
| technical_quality_score | 0.1271 | 0.3867 | 0.4609 | 0.5924 | 0.7960 | 0.1293 | Moderate spread; weighted sum of above fields |

### Advanced Scores (CLIP-based)

| Field | Min | P25 | Median | P75 | Max | Stddev | Notes |
|-------|-----|-----|--------|-----|-----|--------|-------|
| nima_score | 0.5210 | 0.5529 | 0.5555 | 0.5595 | 0.8017 | **0.0683** | **Critically compressed** — ViT-B-32 text-prompt differential produces nearly identical outputs (p25=0.553, p75=0.560) |
| aesthetic_score | 0.5187 | 0.5476 | 0.5912 | 0.7166 | 0.8785 | **0.0913** | Compressed — power curve (0.75 exponent) pulls high scores down; primary ranking signal is weak |
| keep_score | 0.3542 | 0.5264 | 0.5803 | 0.6968 | 0.8421 | **0.1000** | Moderate spread but unused in any ranking or filtering |
| curation_score | 0.2093 | 0.3653 | 0.4128 | 0.4841 | 0.6731 | **0.0754** | **Critically compressed** — primary sort field; top 10% all below 0.53, gap between #1 and #10 is only ~0.06 |
| semantic_relevance_score | 0.3833 | 0.5617 | 0.5895 | 0.6322 | 1.0000 | **0.0719** | Compressed; heavily biased by camera brand (DSLR +0.25, phone +0.0) |

### Print Scores

| Field | Min | P25 | Median | P75 | Max | Stddev | Notes |
|-------|-----|-----|--------|-----|------|--------|-------|
| print_score_6x8 | 0.1271 | 0.3867 | 0.4609 | 0.5924 | 0.7960 | 0.1293 | = technical_quality_score (no aspect ratio adjustment) |
| print_score_8x10 | 0.1207 | 0.3674 | 0.4379 | 0.5628 | 0.7562 | 0.1229 | = tech * 0.95 (no aspect ratio adjustment) |
| print_score_12x18 | 0.1144 | 0.3480 | 0.4148 | 0.5332 | 0.7164 | 0.1164 | = tech * 0.90 (no aspect ratio adjustment) |

**Key insight:** Print scores are pure scalings of technical quality with zero aspect-ratio consideration. Given that 77.3% of photos match the 6x8 print ratio (4:3), and only ~2.2% natively match 12x18 (1.5:1), this is a major gap.

## Cross-Score Correlations

### Camera type comparison

| Category | Count | Avg Curation | Avg Aesthetic | Avg Tech Quality |
|----------|-------|-------------|---------------|-----------------|
| Phone/other | 12,961 | 0.4157 | **0.6366** | 0.4816 |
| DSLR/mirrorless | 4,125 | **0.4332** | 0.6074 | **0.4687** |

**Key insight:** Phone photos have **higher aesthetic scores** (0.637 vs 0.607) but DSLR photos get higher curation scores due to the semantic_relevance camera brand bonus (+0.25 for DSLR). This means curation_score is biased toward gear, not photo quality. The dataset contradicts the assumption that DSLR = better aesthetics.

## Identified Problems and Fixes

### Problem 1: nima_score critically compressed (stddev=0.068)
- **Root cause:** ViT-B-32 with text-prompt differential scoring produces nearly identical outputs for all photos
- **Fix:** Switch to `ViT-H-14` with LAION-Aesthetic v2 pretrained weights (dedicated aesthetic model, not CLIP text-matching). Add temperature scaling (t=0.1) and percentile normalization for better spread.

### Problem 2: curation_score critically compressed (stddev=0.075)
- **Root cause:** Formula `(0.5 * tech_quality) + (0.3 * semantic_relevance)` ignores aesthetic_score entirely; semantic_relevance has DSLR bias
- **Fix:** `curation = (0.4 * aesthetic_norm) + (0.3 * keep_norm) + (0.2 * tech_quality_norm) + (0.1 * semantic_norm)` — remove camera brand bonus, add aesthetic and keep scores

### Problem 3: Print scores ignore aspect ratio
- **Root cause:** Pure scaling of technical quality with no cropping penalty
- **Fix:** Compute aspect-ratio mismatch penalty per print size; apply as multiplicative factor to base score

### Problem 4: entropy_score not discriminative (stddev=0.10)
- **Root cause:** Natural photos all have similar histogram distributions
- **Fix:** Reduce weight in technical_quality_score from 0.15 to 0.08; increase noise_score weight from 0.15 to 0.20

### Problem 5: brightness scoring uses linear mapping
- **Root cause:** `abs(brightness - 0.65)` doesn't match human perception (logarithmic)
- **Fix:** Use gamma-corrected brightness; target optimal range of 0.55–0.75 instead of single point

### Problem 6: semantic_relevance has DSLR bias (+0.25 for Canon/Nikon/Sony)
- **Root cause:** Camera brand bonus inflates curation_score for DSLR photos regardless of actual quality
- **Fix:** Remove camera brand bonus entirely; rely on technical_quality and aesthetic scores which already capture image quality

### Problem 7: keep_score unused
- **Root cause:** Computed but no sort option, no filtering, no UI affordance
- **Fix:** Add `keep_desc`/`keep_asc` sort options to API; promote to ranking dimension in curation formula

## Recommended CLIP Model Configuration

| Setting | Current | Recommended | Reason |
|---------|---------|-------------|--------|
| Model | ViT-B-32 | ViT-H-14 (or ViT-g-14) | Dedicated aesthetic model with LAION-Aesthetic v2 weights; much better discrimination |
| Scoring method | Text-prompt differential | LAION-Aesthetic v2 (0–10 score regression) | Purpose-built for photo aesthetics, not text matching |
| Temperature | N/A | 0.1 | Sharpen output distribution when using percentile normalization |
| Normalization | None | Percentile-based per-run | Compensates for model calibration drift across runs |

## Print Size Aspect Ratios (for cropping penalty calculation)

| Print Size | Ratio | Matches Dataset? |
|------------|-------|-----------------|
| 6x8 | 1.333 (4:3) | Yes — 77.3% of photos match natively |
| 8x10 | 1.250 (5:4) | Partial — ~15% match; most need minor crop |
| 12x18 | 1.500 (3:2) | Rare — only ~2.2% of photos match natively |

## Implementation Priority

1. **High:** Switch CLIP model to ViT-H-14 with LAION-Aesthetic v2 weights + temperature/normalization
2. **High:** Fix curation_score formula (add aesthetic, remove DSLR bias)
3. **Medium:** Aspect-ratio-aware print scores
4. **Medium:** Add keep_score sort options to API
5. **Low:** Brightness gamma correction
6. **Low:** Reduce entropy weight in technical_quality
