# Dataset Registry and Governance

## Overview

This project uses **complementary data fusion** rather than treating any single
source as representative of German household waste. TACO contributes real-world
images with clutter, varied lighting, and object-level COCO annotations.
TrashNet contributes six material classes photographed against a clean,
consistent background, which is useful as a controlled reference set. The
Kaggle Waste Classification Data adds a larger set with an `O` (Organic) class,
providing additional examples relevant to `Bioabfall`; its `R` (Recyclable)
class is broad and cannot by itself distinguish the German recycling streams.

The sources differ in collection context, labels, class balance, and annotation
quality. Keep source identity and original labels in any derived dataset, record
the mapping version, and split data by source or original image identity where
possible to reduce leakage. The mapping below is a starting point for review,
not an authoritative disposal decision. Verify the licenses for both the
repository and the underlying image assets before redistribution or publication.

## Dataset Comparison

| Dataset | Version / commit | Official license | Approx. images | Annotation format | Official source |
|---|---|---|---:|---|---|
| TACO (Trash Annotations in Context) | GitHub `master` (mutable; downloader uses the current branch contents) | MIT for the repository; individual Flickr image rights may differ | 1,500 | COCO JSON (`annotations.json`), with 60 original categories and about 4,784 annotations | [pedropro/TACO](https://github.com/pedropro/TACO) |
| TrashNet | GitHub `master` (mutable; downloader uses the current branch contents) | MIT for the repository; verify rights for image assets before reuse | 2,527 | Directories by class: `glass`, `paper`, `cardboard`, `plastic`, `metal`, `trash` | [garythung/trashnet](https://github.com/garythung/trashnet) |
| Waste Classification Data | Kaggle dataset version 1 | CC BY-SA 4.0 (Kaggle dataset metadata) | About 25,077 | Directories by split and class: `TRAIN` / `TEST`, `O` (Organic) / `R` (Recyclable) | [techsash/waste-classification-data](https://www.kaggle.com/datasets/techsash/waste-classification-data) |

The TACO and TrashNet branch references are not immutable identifiers. For
reproducible experiments, record the resolved Git commit or archive checksum,
download date, Kaggle version, and any local filtering or relabeling in the
experiment metadata. Dataset versions and source contents can change.

## Dataset Details

### TACO — Trash Annotations in Context

- **Source:** [https://github.com/pedropro/TACO](https://github.com/pedropro/TACO)
- **Scale and labels:** Approximately 1,500 real-world images, about 4,784
  object annotations, and 60 original categories.
- **Annotations:** COCO-format JSON downloaded from
  `https://raw.githubusercontent.com/pedropro/TACO/master/data/annotations.json`.
  The downloader retrieves each image from its URL in the COCO image record and
  stores it under the corresponding relative `file_name`.
- **License and provenance:** The upstream repository declares MIT. Image URLs
  point to third-party Flickr assets, whose rights can be different; inspect
  image-level attribution and license metadata before reuse.
- **Role in this project:** Realistic contexts and object-level labels for
  robustness evaluation and possible object-crop experiments.

### TrashNet

- **Source:** [https://github.com/garythung/trashnet](https://github.com/garythung/trashnet)
- **Scale and labels:** 2,527 images in six classes: `glass`, `paper`,
  `cardboard`, `plastic`, `metal`, and `trash`.
- **Annotations:** Class labels are represented by directories rather than
  bounding boxes or per-image metadata.
- **License and provenance:** The upstream repository declares MIT. Check any
  separate terms applicable to the image assets before redistribution.
- **Role in this project:** A clean-background reference set for controlled
  material classification and traditional feature-based baselines.

### Waste Classification Data (Kaggle)

- **Source:**
  [https://www.kaggle.com/datasets/techsash/waste-classification-data](https://www.kaggle.com/datasets/techsash/waste-classification-data)
- **Scale and labels:** Approximately 25,077 images in the `O` (Organic) and
  `R` (Recyclable) classes, arranged into training and test splits.
- **Annotations:** Directory labels by split and class; this is binary
  supervision, not a five-way German waste label.
- **License:** CC BY-SA 4.0, as stated in the Kaggle dataset metadata. Preserve
  attribution and comply with the share-alike terms for adapted material.
- **Role in this project:** Additional image volume and organic examples
  relevant to `Bioabfall`. The `R` class should only be used as broad
  recyclable supervision unless finer labels are independently verified.

## Preliminary German Recycling Mapping

This mapping is provisional. Material condition, local municipal rules, and
packaging composition affect the correct bin. Ambiguous examples should be
reviewed or retained as unknown rather than assigned a confident five-way
label.

| Source | Original label(s) | Preliminary German category | Mapping notes |
|---|---|---|---|
| TACO | Plastic bottle/container, can, aerosol can, aluminum foil, composite packaging | `Gelber Sack` | Packaging materials only; contamination or non-packaging items may change disposal. |
| TACO | Paper, cardboard, paper bag | `Papier` | Only clean, dry paper/cardboard; soiled items need review. |
| TACO | Glass bottle/jar | `Altglas` | Packaging glass; color separation is outside this initial mapping. |
| TACO | Food waste / food scraps | `Bioabfall` | Confirm the original category and that the item is accepted as organic waste. |
| TACO | Cigarette butt, hygiene item, dirty/unknown composite, other non-recyclable item | `Restmüll` (provisional) | Inspect source labels; the broad `other` category is not automatically residual waste. |
| TrashNet | `glass` | `Altglas` (provisional) | The class may include glass objects that are not packaging. |
| TrashNet | `paper`, `cardboard` | `Papier` | Assumes clean paper and cardboard. |
| TrashNet | `plastic`, `metal` | `Gelber Sack` (provisional) | Class labels do not establish that an item is packaging. |
| TrashNet | `trash` | `Restmüll` (provisional) | A mixed class; inspect or exclude ambiguous samples. |
| Kaggle | `O` (Organic) | `Bioabfall` (weak/provisional) | Organic is broader than accepted household bio-waste; verify items where possible. |
| Kaggle | `R` (Recyclable) | **No direct five-way mapping** | Contains no reliable distinction among `Gelber Sack`, `Papier`, and `Altglas`; use only for binary pretraining/auxiliary supervision or relabel verified examples. |

## Local Directory Structure

After running the downloader from the repository root, `data/raw/` is organized
as follows. The TrashNet archive keeps its upstream class-directory layout, and
the Kaggle download keeps its provided split/class directories.

```text
data/raw/
├── trashnet/                 # Extracted upstream repository/data
│   └── <upstream class/data files>
├── taco/
│   ├── annotations.json      # COCO annotations
│   └── images/
│       └── <COCO file_name paths>
└── kaggle/
    └── <TRAIN|TEST>/<O|R>/  # Extracted Kaggle archive
```

`data/raw/` and its contents are ignored by Git to keep large datasets and
downloaded images out of version control. This registry remains tracked as
`data/README.md`; do not commit credentials or raw data.

## Reproducibility and Download Instructions

From the repository root, install the project dependencies and download all
sources:

```bash
python3 -m pip install -r requirements.txt
python3 src/data/download_datasets.py --dataset all --output-dir data/raw
```

Download a single source, or fetch a small TACO sample for a quick test:

```bash
python3 src/data/download_datasets.py --dataset trashnet --output-dir data/raw
python3 src/data/download_datasets.py --dataset taco --output-dir data/raw
python3 src/data/download_datasets.py --dataset taco --output-dir data/raw --limit 25
python3 src/data/download_datasets.py --dataset kaggle --output-dir data/raw
```

TACO and TrashNet downloads do not require credentials. Kaggle requires an API
token:

1. In Kaggle account settings, create an API token and download `kaggle.json`.
2. On Linux, place it in the standard location and restrict its permissions:

   ```bash
   mkdir -p ~/.kaggle
   cp ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
   chmod 600 ~/.kaggle/kaggle.json
   ```

   Alternatively, export both `KAGGLE_USERNAME` and `KAGGLE_KEY` in the
   current shell. Do not commit the token file or put its values in source
   control.
3. Run the Kaggle command above. If credentials are absent, the script prints
   these setup instructions and skips Kaggle without blocking other sources.

For each experiment, record source versions/commits, Kaggle version, download
date, selected sample limit, and any mapping or filtering decisions.
