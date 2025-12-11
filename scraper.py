"""
Benco Dental Scraper.
Extracts products from shop.benco.com
"""

import requests
from bs4 import BeautifulSoup
import base64
import gzip
import json
import re
from typing import Optional

from models import Config


class BencoScraper:
    """Class responsible for extracting data from Benco pages"""

    BASE_URL = 'https://shop.benco.com'

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)

    def build_query_param(self, category: str, page: int = 1) -> str:
        """
        Builds the encoded 'q' parameter for the search.
        The parameter is JSON compressed with gzip and encoded in Base64.
        """
        data = {
            "Categorization": {
                "Tab": category,
                "TabId": 0,
                "CategoryId": 0
            },
            "Page": page,
            "GroupSimilarItems": True,
            "AllowAutoCorrectSubstitution": False,
            "Source": f"Categories.{category.replace(' ', '').replace('&', '')}",
            "ShowResultsAsGrid": True,
            "IncludePricing": False,
            "IsCompleteCart": False,
            "IsGeneralSuggestion": False,
            "SelectionCriterionDescription": category
        }

        json_str = json.dumps(data, separators=(',', ':'))
        compressed = gzip.compress(json_str.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('utf-8')
        return encoded

    def fetch_page(self, category: str, page: int) -> Optional[str]:
        """
        Makes the HTTP request to get a product page.
        Returns None if there is an error.
        """
        try:
            params = {'q': self.build_query_param(category, page)}
            response = self.session.get(
                f'{self.BASE_URL}/Search',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"  [ERROR] Página {page}: {e}")
            return None

    def parse_products(self, html: str, seen_skus: set, category_name: str) -> tuple[list[dict], int, int]:
        """
        Extracts products from the page HTML.

        Args:
            html: Page HTML
            seen_skus: Set of already seen SKUs to avoid duplicates
            category_name: Category name (from .env)

        Returns:
            Tuple with (extracted products, total detected, skipped)
        """
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        detected = 0
        skipped = 0

        # Extract ratings from JSON-LD
        ratings_map = self._extract_ratings_from_jsonld(soup)

        product_grid = soup.find('div', class_='product-grid')
        if not product_grid:
            return products, detected, skipped

        items = product_grid.find_all('div', recursive=False)

        for item in items:
            detected += 1

            # Base structure with all keys
            product = {
                'sku': '',
                'name': '',
                'price': '',
                'availability': '',
                'brand': '',
                'product_category': '',
                'image_url': '',
                'product_url': '',
                'rating': '',
                'review_count': ''
            }

            # Find product link for SKU and name
            link = item.find('a', href=re.compile(r'/Product/'))
            if not link:
                skipped += 1
                continue

            href = link.get('href', '')

            # Extract SKU from href
            sku_match = re.search(r'/Product/([^/]+)/', href)
            if not sku_match:
                skipped += 1
                continue

            sku = sku_match.group(1)

            # Skip duplicates
            if sku in seen_skus:
                skipped += 1
                continue

            product['sku'] = sku
            seen_skus.add(sku)

            # Product URL
            product['product_url'] = f"{self.BASE_URL}{href.split('?')[0]}"

            # Product name - clean extra text
            raw_name = link.get_text(strip=True)
            clean_name = re.sub(
                r'(No Longer Available|In Stock.*|Out of Stock|Estimated Ship Date.*|\d{4}-\d{3}).*$',
                '',
                raw_name
            ).strip()
            product['name'] = clean_name

            # Product image
            img = item.find('img')
            if img:
                product['image_url'] = img.get('src', '')

            # Extract availability
            product['availability'] = self._extract_availability(item)

            # Extract price and brand from onclick
            price, brand = self._extract_from_onclick(item)
            product['price'] = price
            product['brand'] = brand
            product['product_category'] = category_name

            # Find rating by product name
            if clean_name in ratings_map:
                product['rating'] = ratings_map[clean_name].get('rating', '')
                product['review_count'] = ratings_map[clean_name].get('review_count', '')

            products.append(product)

        return products, detected, skipped

    def _extract_ratings_from_jsonld(self, soup: BeautifulSoup) -> dict:
        """Extracts product ratings from JSON-LD scripts."""
        ratings_map = {}

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'AggregateRating':
                    item_reviewed = data.get('itemReviewed', {})
                    product_name = item_reviewed.get('name', '')
                    if product_name:
                        ratings_map[product_name] = {
                            'rating': data.get('ratingValue', ''),
                            'review_count': data.get('ratingCount', '')
                        }
            except (json.JSONDecodeError, TypeError):
                continue

        return ratings_map

    def _extract_availability(self, item) -> str:
        """Extracts the product availability text."""
        stock_patterns = [
            r'Estimated Ship Date \d{1,2}/\d{1,2}/\d{2,4}(?: - \d{1,2}/\d{1,2}/\d{2,4})?',
            r'In Stock in \w+',
            r'In Stock',
            r'Out of Stock',
            r'No Longer Available',
            r'Ships in \d+ (?:day|week|business day)s?'
        ]

        item_text = item.get_text()
        for pattern in stock_patterns:
            match = re.search(pattern, item_text, re.I)
            if match:
                return match.group(0).strip()

        return ''

    def _extract_from_onclick(self, item) -> tuple[str, str]:
        """
        Extracts price and brand from the Add to Cart button onclick.
        Format: QuantityChangeClick('SKU', 1, 'uuid', undefined, `Name`, 'Price', `Brand`, 'Category')
        """
        price = ''
        brand = ''

        add_to_cart_btn = item.find('button', class_='add-to-cart-button')
        if add_to_cart_btn:
            onclick = add_to_cart_btn.get('onclick', '')

            price_match = re.search(r"`,\s*'([\d.]+)'", onclick)
            if price_match:
                price = price_match.group(1)

            brand_match = re.search(r"'[\d.]+',\s*`([^`]+)`", onclick)
            if brand_match:
                brand = brand_match.group(1)

        return price, brand

    def get_category_info(self, html: str) -> dict:
        """Extracts category information from JSON-LD."""
        soup = BeautifulSoup(html, 'html.parser')

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'OfferCatalog':
                    return {
                        'name': data.get('name', ''),
                        'total_products': int(data.get('numberOfItems', 0)),
                        'url': data.get('url', '')
                    }
            except (json.JSONDecodeError, TypeError):
                continue

        return {'name': '', 'total_products': 0, 'url': ''}
