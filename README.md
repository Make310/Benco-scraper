# Benco Dental Web Scraper

Scraper para extraer productos de [shop.benco.com](https://shop.benco.com).

## Datos Extraídos

| Campo | Descripción |
|-------|-------------|
| `sku` | Identificador único del producto |
| `name` | Nombre del producto |
| `price` | Precio (cuando está disponible) |
| `availability` | Estado de stock / fecha de envío |
| `brand` | Marca del fabricante |
| `product_category` | Categoría del producto |
| `image_url` | URL de la imagen |
| `product_url` | URL del producto |
| `rating` | Calificación promedio |
| `review_count` | Número de reviews |

## Instalación

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Editar el archivo `.env`:

```env
# Categoría a scrapear (nombre exacto del sitio)
CATEGORY_NAME=Acrylics & Relines

# Páginas a scrapear (0 = todas)
MAX_PAGES=2

# Delay entre peticiones (segundos)
MIN_DELAY=1
MAX_DELAY=3

# Tipo de almacenamiento: json o sqlite
STORAGE_TYPE=json

# Salida JSON (cuando STORAGE_TYPE=json)
OUTPUT_FILE=productos.json

# Base de datos SQLite (cuando STORAGE_TYPE=sqlite)
DB_PATH=productos.db
```

### Categorías de ejemplo

- `Acrylics & Relines`
- `Alloy`
- `Anesthetic`
- `Articulating`

> El nombre debe coincidir exactamente con el sitio web.

## Ejecución

```bash
python main.py
```

### Salida esperada

```
==================================================
BENCO DENTAL SCRAPER
==================================================
Categoría: Acrylics & Relines
Max páginas: 2
Delay: 1.0-3.0s
==================================================

[Página 1/2]
  Categoría: Acrylics and Relines
  Total en sitio: 1353 productos (57 páginas)
  Detectados: 24 | Guardados: 24 | Omitidos: 0
  Esperando 2.3s...
[Página 2/2]
  Detectados: 24 | Guardados: 24 | Omitidos: 0

Guardado en: productos.json

==================================================
ESTADÍSTICAS DE LA CORRIDA
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

## Estructura del Proyecto

```
test_scraping/
├── main.py            # Orquestador principal
├── scraper.py         # Extracción de datos (BencoScraper)
├── storage.py         # Persistencia (JSON / SQLite)
├── models.py          # Modelos de datos
├── .env               # Configuración
├── .gitignore         # Archivos ignorados
├── requirements.txt   # Dependencias
└── README.md
```

## Arquitectura

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

| Módulo | Responsabilidad |
|--------|-----------------|
| `models.py` | Estructuras de datos (Config, Statistics) |
| `scraper.py` | Extracción HTTP y parsing HTML |
| `storage.py` | Persistencia con patrón Strategy |
| `main.py` | Orquestación del flujo |

## Almacenamiento

### JSON (default)

```env
STORAGE_TYPE=json
OUTPUT_FILE=productos.json
```

Genera un archivo JSON con estadísticas y productos.

### SQLite

```env
STORAGE_TYPE=sqlite
DB_PATH=productos.db
```

Crea tablas `products` y `statistics`. Los SKUs duplicados se omiten automáticamente.

```bash
# Consultar datos
sqlite3 productos.db "SELECT sku, name, price FROM products LIMIT 5;"
```

## Formato de Salida (JSON)

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

## Estadísticas

| Campo | Descripción |
|-------|-------------|
| `categoryUrl` | URL de la categoría |
| `totalDetected` | Productos encontrados |
| `totalSaved` | Productos guardados (únicos) |
| `totalSkipped` | Productos omitidos |
| `missingPrice` | Productos sin precio |
| `startedAt` | Inicio de ejecución |
| `finishedAt` | Fin de ejecución |
| `durationSeconds` | Duración total |

## Limitaciones

- **Precios**: Solo disponibles para productos con botón "Add to Cart"
- **Rate limiting**: Usar delays de 1-3 segundos
- **Paginación**: 24 productos por página

## Dependencias

```
requests>=2.28.0
beautifulsoup4>=4.11.0
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
```
