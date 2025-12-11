"""
Modelos de datos para el scraper.
"""

import os
import json
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass
class Config:
    """Configuración del scraper cargada desde .env"""
    category_name: str = field(default_factory=lambda: os.getenv('CATEGORY_NAME', 'Acrylics & Relines'))
    max_pages: int = field(default_factory=lambda: int(os.getenv('MAX_PAGES', '2')))
    min_delay: float = field(default_factory=lambda: float(os.getenv('MIN_DELAY', '1')))
    max_delay: float = field(default_factory=lambda: float(os.getenv('MAX_DELAY', '3')))
    output_file: str = field(default_factory=lambda: os.getenv('OUTPUT_FILE', 'productos.json'))

    # Storage configuration
    storage_type: str = field(default_factory=lambda: os.getenv('STORAGE_TYPE', 'json'))
    db_path: str = field(default_factory=lambda: os.getenv('DB_PATH', 'productos.db'))

    headers: dict = field(default_factory=lambda: {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    })


@dataclass
class Statistics:
    """Estadísticas de la corrida del scraper"""
    categoryUrl: str = ''
    totalDetected: int = 0
    totalSaved: int = 0
    totalSkipped: int = 0
    missingPrice: int = 0
    startedAt: str = ''
    finishedAt: str = ''
    durationSeconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def print_summary(self):
        """Imprime el resumen de estadísticas en consola."""
        print("\n" + "=" * 50)
        print("ESTADÍSTICAS DE LA CORRIDA")
        print("=" * 50)
        print(json.dumps(self.to_dict(), indent=2))
        print("=" * 50)
