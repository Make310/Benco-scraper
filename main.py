"""
Benco Dental Web Scraper
========================
Punto de entrada principal y orquestación del scraping.

Uso:
    python main.py
"""

import time
import random
from datetime import datetime

from models import Config, Statistics
from scraper import BencoScraper
from storage import StorageFactory


class Orchestrator:
    """Clase que coordina el flujo completo del scraping"""

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
        """Aplica un delay aleatorio entre peticiones."""
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        print(f"  Esperando {delay:.1f}s...")
        time.sleep(delay)

    def run(self) -> dict:
        """Ejecuta el proceso completo de scraping."""
        # Iniciar estadísticas
        start_time = datetime.now()
        self.stats.startedAt = start_time.strftime('%Y-%m-%d %H:%M:%S')

        print("=" * 50)
        print("BENCO DENTAL SCRAPER")
        print("=" * 50)
        print(f"Categoría: {self.config.category_name}")
        print(f"Max páginas: {self.config.max_pages}")
        print(f"Delay: {self.config.min_delay}-{self.config.max_delay}s")
        print("=" * 50 + "\n")

        all_products = []
        seen_skus = set()
        category_info = {}
        total_pages_to_scrape = self.config.max_pages

        # Scrapear páginas
        for page in range(1, total_pages_to_scrape + 1):
            print(f"[Página {page}/{total_pages_to_scrape}]")

            # Fetch de la página
            html = self.scraper.fetch_page(self.config.category_name, page)

            if html is None:
                print(f"  [SKIP] Página {page} falló, continuando...")
                continue

            # En la primera página, obtener info de la categoría
            if page == 1:
                category_info = self.scraper.get_category_info(html)
                self.stats.categoryUrl = category_info.get('url', '')
                total = category_info.get('total_products', 0)
                total_pages = (total // 24) + (1 if total % 24 else 0)
                print(f"  Categoría: {category_info.get('name')}")
                print(f"  Total en sitio: {total} productos ({total_pages} páginas)")

                # Ajustar max_pages si es 0 (todas las páginas)
                if self.config.max_pages == 0:
                    total_pages_to_scrape = total_pages

            # Parsear productos
            products, detected, skipped = self.scraper.parse_products(html, seen_skus, self.config.category_name)

            # Actualizar estadísticas
            self.stats.totalDetected += detected
            self.stats.totalSkipped += skipped
            self.stats.totalSaved += len(products)

            all_products.extend(products)
            print(f"  Detectados: {detected} | Guardados: {len(products)} | Omitidos: {skipped}")

            # Delay entre páginas (excepto la última)
            if page < total_pages_to_scrape:
                self._random_delay()

        # Calcular productos sin precio
        self.stats.missingPrice = sum(1 for product in all_products if product['price'] == '')

        # Finalizar estadísticas
        end_time = datetime.now()
        self.stats.finishedAt = end_time.strftime('%Y-%m-%d %H:%M:%S')
        self.stats.durationSeconds = round((end_time - start_time).total_seconds(), 2)

        # Preparar datos de salida
        output_data = {
            'statistics': self.stats.to_dict(),
            'products': all_products
        }

        # Guardar datos
        output_location = self.config.db_path if self.config.storage_type == 'sqlite' else self.config.output_file
        if self.storage.save(output_data):
            print(f"\nGuardado en: {output_location}")

        # Imprimir estadísticas
        self.stats.print_summary()

        return output_data


def main():
    """Punto de entrada principal."""
    config = Config()
    orchestrator = Orchestrator(config)
    orchestrator.run()


if __name__ == '__main__':
    main()
