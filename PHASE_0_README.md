# Phase 0: Vedic Knowledge Data Collection

This phase scrapes and parses all Vedic knowledge sources into a unified dataset.

## Components

### 1. **PDF Parser** (`src/data_pipeline/pdf_parser.py`)
- Extracts verses from local Bhagavad Gita PDFs
- Uses `pdfplumber` (or `PyPDF2` fallback) for reliable extraction
- Outputs: `data/pdf_extracted/bhagavad_gita_pdf.json`
- Produces ~700 verses with chapter/verse structure

### 2. **VedaBase Scraper** (`src/data_pipeline/vedabase_scraper.py`)
- Scrapes **ALL English books** from vedabase.io by parsing the rendered
  `https://vedabase.io/en/library/...` pages (the site's old `/api/...`
  JSON endpoints have been retired and now 404 — it was rebuilt on Next.js)
  - Bhagavad Gita
  - Srimad Bhagavatam
  - Chaitanya Charitamrita
  - Other Puranas, Upanishads, commentaries
- Fetches verses, transliteration, synonyms, translation, and purports (commentaries)
- Rate-limited to 10s between requests by default, honoring vedabase.io's
  `robots.txt` `Crawl-delay: 10` (override with `VEDABASE_RATE_LIMIT`, but
  don't go below the site's stated delay)
- Outputs: `data/vedabase_raw/vedabase_data.json` + summary
- Produces: 10,000+ verses across multiple texts

### 3. **Vanipedia Scraper** (`src/data_pipeline/vanipedia_scraper.py`)
- Extracts Vedic concepts and definitions from vanipedia.org via its real
  MediaWiki API (`/w/api.php`) — the REST endpoints the previous version
  targeted (`/api/search`, `/api/concepts/<id>`) never existed
- Core concepts: Dharma, Bhakti, Yoga, Karma, Atman, Brahman, Krishna, etc.
- Filters out non-English article variants (e.g. `ES/...` Spanish pages)
- Outputs: `data/vanipedia_raw/concepts.json`
- Produces: 20+ core concepts, each with several matching articles

### 4. **Pipeline Orchestrator** (`src/data_pipeline/pipeline.py`)
- Runs all three components in sequence
- Merges data (PDF + VedaBase + Vanipedia)
- Validates consistency
- Generates summary report
- Outputs:
  - `data/pipeline_output/pipeline_complete.json` (summary)
  - `data/pipeline_output/merged_verses.json` (unified verses)
  - `data/pipeline_output/concepts.json` (all concepts)

## Running Phase 0

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline
python src/data_pipeline/pipeline.py
```

### Individual Components

```bash
# PDF Parser only
python src/data_pipeline/pdf_parser.py

# VedaBase Scraper only
python src/data_pipeline/vedabase_scraper.py

# Vanipedia Scraper only
python src/data_pipeline/vanipedia_scraper.py
```

## Output Structure

```
data/
├── pdf_extracted/
│   └── bhagavad_gita_pdf.json          # 700 verses from PDF
├── vedabase_raw/
│   ├── vedabase_data.json              # All VedaBase books & verses
│   └── scrape_summary.json             # Summary stats
├── vanipedia_raw/
│   └── concepts.json                   # Concepts & definitions
└── pipeline_output/
    ├── pipeline_complete.json          # Final summary
    ├── merged_verses.json              # Unified verses with cross-refs
    └── concepts.json                   # Consolidated concepts
```

## Data Schema

### Merged Verse Format
```json
{
  "BG 1.1": {
    "reference": "BG 1.1",
    "chapter": 1,
    "verse": 1,
    "sources": {
      "pdf": "Sanskrit text and Prabhupada translation...",
      "vedabase": "Alternative translation, word meanings, purports..."
    },
    "concepts": ["Dharma", "War", "Righteousness"]
  }
}
```

### Concept Format
```json
{
  "dharma": {
    "id": "dharma",
    "title": "Dharma",
    "definition": "...",
    "description": "...",
    "references": [...],
    "synonyms": ["duty", "righteousness"],
    "related_concepts": ["karma", "yoga"],
    "url": "https://vanipedia.org/..."
  }
}
```

## Next Steps

Once Phase 0 completes:

1. **Phase A**: Transform merged data into Obsidian vault structure
   - Organize by concept hierarchies
   - Create wikilinks for cross-references
   - Generate frontmatter with metadata

2. **Phase B**: Build RAG pipeline
   - Embed verses with BAAI/bge-small
   - Store in PostgreSQL + pgvector
   - Implement hybrid retrieval

3. **Phase C**: Create chat interface
   - CLI with Typer
   - Multi-turn conversation
   - Citation + source display

## Configuration

### Environment Variables
- `DEEPSEEK_API_KEY` — Optional, for Phase B LLM (falls back to Ollama)
- `VEDABASE_RATE_LIMIT` — Delay between API requests (default: 0.2s)
- `VANIPEDIA_RATE_LIMIT` — Delay between Vanipedia requests (default: 0.3s)

### Logging
All scrapers log progress to stdout. For detailed debug output:

```bash
export LOGLEVEL=DEBUG
python src/data_pipeline/pipeline.py
```

## Troubleshooting

### PDF Parser Issues
- **"PDF not found"**: Ensure `data/Bhagavad-Gita As It Is.pdf` exists
- **ImportError (pdfplumber)**: Install with `pip install pdfplumber`

### Network Issues
- **VedaBase page timeout**: Check network, increase timeout in scraper
- **Proxy/firewall blocking**: May need VPN or network policy adjustment
- **`vedabase.io/api/...` returns 404**: expected — that API no longer
  exists. The scraper parses `https://vedabase.io/en/library/...` HTML instead.

### Memory Issues
- Large scrape (10,000+ verses): VedaBase scraper saves incrementally
- Monitor disk space: `df -h data/`

## Estimated Completion Time

- PDF Parser: ~10 seconds (local)
- VedaBase Scraper: with the required 10s crawl-delay, a full scrape of
  10,000+ verses takes **on the order of 1-2 days**, not minutes. Use
  `scrape_all_books(max_books=..., max_chapters_per_book=...)` to pull a
  bounded subset for testing.
- Vanipedia Scraper: ~2-3 minutes (20 concepts, ~1s between requests)

---

**Phase 0 produces the raw knowledge base for Phases A, B, and C.**
