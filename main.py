"""
Benco Dental Web Scraper
========================
Main entry point and scraping orchestration.

Usage:
    python main.py
"""

import time
import random
from datetime import datetime

from models import Config, Statistics
from scraper import BencoScraper
from storage import StorageFactory


class Orchestrator:
    """Class that coordinates the complete scraping flow"""

    def __init__(self, config: Config):
        self.config  = config
        self.scraper = BencoScraper(config)
        self.storage = StorageFactory.create(
            storage_type=config.storage_type,
            filepath=config.output_file,
            db_path=config.db_path
        )
        self.stats = Statistics()

    def _random_delay(self):
        """Applies a random delay between requests."""
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        print(f"  Waiting {delay:.1f}s...")
        time.sleep(delay)

    def run(self) -> dict:
        """Executes the complete scraping process."""
        # Initialize statistics
        start_time = datetime.now()
        self.stats.startedAt = start_time.strftime('%Y-%m-%d %H:%M:%S')

        print("=" * 50)
        print("BENCO DENTAL SCRAPER")
        print("=" * 50)
        print(f"Category: {self.config.category_name}")
        print(f"Max pages: {self.config.max_pages}")
        print(f"Delay: {self.config.min_delay}-{self.config.max_delay}s")
        print("=" * 50 + "\n")

        all_products = []
        seen_skus = set()
        category_info = {}
        total_pages_to_scrape = self.config.max_pages

        # Scrape pages
        for page in range(1, total_pages_to_scrape + 1):
            print(f"[Page {page}/{total_pages_to_scrape}]")

            # Fetch the page
            html = self.scraper.fetch_page(self.config.category_name, page)

            if html is None:
                print(f"  [SKIP] Page {page} failed, continuing...")
                continue

            # On the first page, get category info
            if page == 1:
                category_info = self.scraper.get_category_info(html)
                self.stats.categoryUrl = category_info.get('url', '')
                total = category_info.get('total_products', 0)
                total_pages = (total // 24) + (1 if total % 24 else 0)
                print(f"  Category: {category_info.get('name')}")
                print(f"  Total on site: {total} products ({total_pages} pages)")

                # Adjust max_pages if 0 (all pages)
                if self.config.max_pages == 0:
                    total_pages_to_scrape = total_pages

            # Parse products
            products, detected, skipped = self.scraper.parse_products(html, seen_skus, self.config.category_name)

            # Update statistics
            self.stats.totalDetected += detected
            self.stats.totalSkipped += skipped
            self.stats.totalSaved += len(products)

            all_products.extend(products)
            print(f"  Detected: {detected} | Saved: {len(products)} | Skipped: {skipped}")

            # Delay between pages (except the last one)
            if page < total_pages_to_scrape:
                self._random_delay()

        # Calculate products without price
        self.stats.missingPrice = sum(1 for product in all_products if product['price'] == '')

        # Finalize statistics
        end_time = datetime.now()
        self.stats.finishedAt = end_time.strftime('%Y-%m-%d %H:%M:%S')
        self.stats.durationSeconds = round((end_time - start_time).total_seconds(), 2)

        # Prepare output data
        output_data = {
            'statistics': self.stats.to_dict(),
            'products': all_products
        }

        # Save data
        output_location = self.config.db_path if self.config.storage_type == 'sqlite' else self.config.output_file
        if self.storage.save(output_data):
            print(f"\nSaved to: {output_location}")

        # Print statistics
        self.stats.print_summary()

        return output_data


def main():
    """Main entry point."""
    config = Config()
    orchestrator = Orchestrator(config)
    orchestrator.run()


if __name__ == '__main__':
    main()
