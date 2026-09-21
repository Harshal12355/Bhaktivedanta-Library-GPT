#!/bin/sh
# Collect the corpus, merge the sources, and rebuild the Obsidian vault.
#
#   ./run_phase0.sh                 every book
#   ./run_phase0.sh --books iso,bs  only those books
#   ./run_phase0.sh --list          show the available book ids
#
# Safe to interrupt and re-run: the scraper skips finished chapters without
# issuing a request, so it continues from wherever it stopped.
#
# This deliberately does not call pipeline.py's run_full_pipeline, whose merge
# step would be fed by scrapers re-run from within the same process; here the
# merge reads whatever the scrape has already written to disk.
set -e

cd "$(dirname "$0")"
mkdir -p logs

if [ "$1" = "--list" ]; then
    exec python3 -m src.data_pipeline.vedabase_scraper --list
fi

echo "==> [1/3] Scraping vedabase.io"
python3 -m src.data_pipeline.vedabase_scraper "$@"

# Vanipedia is deliberately not refreshed here. It overwrites its output
# unconditionally, and a degraded run has already replaced 30 good concepts
# with 1. Refresh it deliberately, and check the result, with:
#   python3 -m src.data_pipeline.vanipedia_scraper

echo "==> [2/3] Merging sources"
python3 - <<'PY'
import json
import sys

sys.path.insert(0, "src")
from data_pipeline.pipeline import DataCollectionPipeline


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


pipeline = DataCollectionPipeline()
concepts = load("data/vanipedia_raw/concepts.json", {}).get("concepts", {})
pipeline.pipeline_data["vedabase_books"] = {
    "status": "success",
    "data": load("data/vedabase_raw/vedabase_data.json", {}),
}
pipeline.pipeline_data["pdf_verses"] = {
    "status": "success",
    "verses": load("data/pdf_extracted/bhagavad_gita_pdf.json", {}),
}
pipeline.pipeline_data["vanipedia_concepts"] = {
    "status": "success",
    "concepts": concepts,
    "concepts_count": len(concepts),
}
pipeline._merge_and_validate()
pipeline._save_pipeline_data()
PY

echo "==> [3/3] Building the Obsidian vault"
python3 -m src.vault_builder.obsidian_generator

echo
echo "Done. Open vedic-vault/ in Obsidian."
