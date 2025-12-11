# Benco Dental Web Scraper

Scraper to extract products from [shop.benco.com](https://shop.benco.com).

## Extracted Data

| Field | Description |
|-------|-------------|
| `sku` | Unique product identifier |
| `name` | Product name |
| `price` | Price (when available) |
| `availability` | Stock status / shipping date |
| `brand` | Manufacturer brand |
| `product_category` | Product category |
| `image_url` | Image URL |
| `product_url` | Product URL |
| `rating` | Average rating |
| `review_count` | Number of reviews |

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit the `.env` file:

```env
# Category to scrape (exact site name)
CATEGORY_NAME=Acrylics & Relines

# Pages to scrape (0 = all)
MAX_PAGES=2

# Delay between requests (seconds)
MIN_DELAY=1
MAX_DELAY=3

# Storage type: json or sqlite
STORAGE_TYPE=json

# JSON output (when STORAGE_TYPE=json)
OUTPUT_FILE=productos.json

# SQLite database (when STORAGE_TYPE=sqlite)
DB_PATH=productos.db
```

### Example Categories

- `Acrylics & Relines`
- `Alloy`
- `Anesthetic`
- `Articulating`

> The name must match exactly with the website.

## Execution

```bash
python main.py
```

### Expected Output

```
==================================================
BENCO DENTAL SCRAPER
==================================================
Category: Acrylics & Relines
Max pages: 2
Delay: 1.0-3.0s
==================================================

[Page 1/2]
  Category: Acrylics and Relines
  Total on site: 1353 products (57 pages)
  Detected: 24 | Saved: 24 | Skipped: 0
  Waiting 2.3s...
[Page 2/2]
  Detected: 24 | Saved: 24 | Skipped: 0

Saved to: productos.json

==================================================
RUN STATISTICS
==================================================
{
  "categoryUrl": "https://shop.benco.com/Search?q=...",
  "totalDetected": 48,
  "totalSaved": 48,
  "totalSkipped": 0,
  "missingPrice": 40,
  "startedAt": "2025-12-10 17:30:00",
  "finishedAt": "2025-12-10 17:30:05",
  "durationSeconds": 5.23
}
==================================================
```

## Project Structure

```
test_scraping/
├── main.py            # Main orchestrator
├── scraper.py         # Data extraction (BencoScraper)
├── storage.py         # Persistence (JSON / SQLite)
├── models.py          # Data models
├── .env               # Configuration
├── .gitignore         # Ignored files
├── requirements.txt   # Dependencies
└── README.md
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   main.py   │────>│  scraper.py │     │   storage.py    │
│ Orchestrator│     │ BencoScraper│     │                 │
└──────┬──────┘     └─────────────┘     │  BaseStorage    │
       │                                │       │         │
       │                                │  ┌────┴────┐    │
       └───────────────────────────────>│  │         │    │
                                        │ Json    SQLite  │
                                        └─────────────────┘
```

| Module | Responsibility |
|--------|-----------------|
| `models.py` | Data structures (Config, Statistics) |
| `scraper.py` | HTTP extraction and HTML parsing |
| `storage.py` | Persistence with Strategy pattern |
| `main.py` | Flow orchestration |

## Storage

### JSON (default)

```env
STORAGE_TYPE=json
OUTPUT_FILE=productos.json
```

Generates a JSON file with statistics and products.

### SQLite

```env
STORAGE_TYPE=sqlite
DB_PATH=productos.db
```

Creates `products` and `statistics` tables. Duplicate SKUs are automatically skipped.

```bash
# Query data
sqlite3 productos.db "SELECT sku, name, price FROM products LIMIT 5;"
```

## Output Format (JSON)

```json
{
  "statistics": {
    "categoryUrl": "https://shop.benco.com/Search?q=...",
    "totalDetected": 48,
    "totalSaved": 48,
    "totalSkipped": 0,
    "missingPrice": 40,
    "startedAt": "2025-12-10 17:30:00",
    "finishedAt": "2025-12-10 17:30:05",
    "durationSeconds": 5.23
  },
  "products": [
    {
      "sku": "1002-835",
      "name": "Blue Fastray Custom Tray...",
      "price": "235.9900",
      "availability": "In Stock in FL",
      "brand": "Keystone Dental",
      "product_category": "Acrylics & Relines",
      "image_url": "https://cdn.benco.com/...",
      "product_url": "https://shop.benco.com/Product/...",
      "rating": "5.0",
      "review_count": "1"
    }
  ]
}
```

## Statistics

| Field | Description |
|-------|-------------|
| `categoryUrl` | Category URL |
| `totalDetected` | Products found |
| `totalSaved` | Products saved (unique) |
| `totalSkipped` | Products skipped |
| `missingPrice` | Products without price |
| `startedAt` | Execution start |
| `finishedAt` | Execution end |
| `durationSeconds` | Total duration |

## Limitations

- **Prices**: Only available for products with "Add to Cart" button
- **Rate limiting**: Use delays of 1-3 seconds
- **Pagination**: 24 products per page

## Dependencies

```
requests>=2.28.0
beautifulsoup4>=4.11.0
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
```
