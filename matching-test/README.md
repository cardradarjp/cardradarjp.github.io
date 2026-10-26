# CardRadar image-matching experiment (isolated)

This folder is an **experiment**, not a working card identifier. No files from the production site or its update process are modified.

## Inputs

- Put **cropped individual card images** in `matching-test/queries/`.
- Put reference card images **you are permitted to use** in `matching-test/references/`.
- Optional `matching-test/references.csv` columns: `filename,card_name,card_number`.
- Reference images are **not included**. Do not assume third-party image databases authorize redistribution or commercial use.

## Run

```bash
python -m pip install -r matching-test/requirements.txt
python matching-test/test_matching.py
```

Results: `matching-test/results/candidates.csv` and `index.html`.

For GitHub Actions, upload images to the branch first, then run **Card image matching experiment** manually under Actions. Download the artifact to inspect the HTML/CSV.

**Important:** Scores are similarity rankings, not confidence or verified accuracy. The script does not identify card numbers independently and does not automatically calculate Top-1/Top-3 accuracy. An independently labeled ground-truth dataset is required. No API/scraping or public site publication is performed.
