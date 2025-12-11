"""
Data storage module.
Implements the Strategy pattern to support multiple backends.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


# ===========================================
# SQLALCHEMY MODEL
# ===========================================

class ProductModel(Base):
    """Product model for SQLAlchemy"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(String, default='')
    availability = Column(String, default='')
    brand = Column(String, default='')
    product_category = Column(String, default='')
    image_url = Column(String, default='')
    product_url = Column(String, default='')
    rating = Column(String, default='')
    review_count = Column(String, default='')
    created_at = Column(DateTime, default=datetime.now)


class StatisticsModel(Base):
    """Statistics model for SQLAlchemy"""
    __tablename__ = 'statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_url = Column(String, default='')
    total_detected = Column(Integer, default=0)
    total_saved = Column(Integer, default=0)
    total_skipped = Column(Integer, default=0)
    missing_price = Column(Integer, default=0)
    started_at = Column(String, default='')
    finished_at = Column(String, default='')
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)


# ===========================================
# BASE ABSTRACT CLASS
# ===========================================

class BaseStorage(ABC):
    """Base abstract class for storage"""

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> bool:
        """
        Saves the extracted data.

        Args:
            data: Dictionary with 'statistics' and 'products'

        Returns:
            True if saved successfully, False on error
        """
        pass


# ===========================================
# JSON IMPLEMENTATION
# ===========================================

class JsonStorage(BaseStorage):
    """Storage in JSON format"""

    def __init__(self, filepath: str, indent: int = 2):
        self.filepath = filepath
        self.indent = indent

    def save(self, data: Dict[str, Any]) -> bool:
        """Saves the data in JSON format."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=self.indent, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"[ERROR] Could not save JSON file: {e}")
            return False


# ===========================================
# SQLALCHEMY IMPLEMENTATION
# ===========================================

class SqlAlchemyStorage(BaseStorage):
    """Storage in SQLite database using SQLAlchemy"""

    def __init__(self, db_path: str = 'productos.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, data: Dict[str, Any]) -> bool:
        """Saves the data in SQLite."""
        try:
            session = self.Session()

            # Save statistics
            stats_data = data.get('statistics', {})
            stats = StatisticsModel(
                category_url=stats_data.get('categoryUrl', ''),
                total_detected=stats_data.get('totalDetected', 0),
                total_saved=stats_data.get('totalSaved', 0),
                total_skipped=stats_data.get('totalSkipped', 0),
                missing_price=stats_data.get('missingPrice', 0),
                started_at=stats_data.get('startedAt', ''),
                finished_at=stats_data.get('finishedAt', ''),
                duration_seconds=stats_data.get('durationSeconds', 0.0)
            )
            session.add(stats)

            # Save products
            products = data.get('products', [])
            saved_count = 0
            skipped_count = 0

            for product_data in products:
                # Check if SKU already exists
                existing = session.query(ProductModel).filter_by(
                    sku=product_data.get('sku', '')
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                product = ProductModel(
                    sku=product_data.get('sku', ''),
                    name=product_data.get('name', ''),
                    price=product_data.get('price', ''),
                    availability=product_data.get('availability', ''),
                    brand=product_data.get('brand', ''),
                    product_category=product_data.get('product_category', ''),
                    image_url=product_data.get('image_url', ''),
                    product_url=product_data.get('product_url', ''),
                    rating=product_data.get('rating', ''),
                    review_count=product_data.get('review_count', '')
                )
                session.add(product)
                saved_count += 1

            session.commit()
            session.close()

            print(f"  [DB] Saved: {saved_count} | Already existed: {skipped_count}")
            return True

        except Exception as e:
            print(f"[ERROR] Could not save to database: {e}")
            return False


# ===========================================
# FACTORY
# ===========================================

class StorageFactory:
    """Factory to create storage instances based on configuration"""

    @staticmethod
    def create(storage_type: str, **kwargs) -> BaseStorage:
        """
        Creates a storage instance based on the specified type.

        Args:
            storage_type: 'json' or 'sqlite'
            **kwargs: Additional arguments for the storage
                - json: filepath, indent
                - sqlite: db_path

        Returns:
            BaseStorage instance
        """
        storage_type = storage_type.lower()

        if storage_type == 'json':
            return JsonStorage(
                filepath=kwargs.get('filepath', 'productos.json'),
                indent=kwargs.get('indent', 2)
            )
        elif storage_type == 'sqlite':
            return SqlAlchemyStorage(
                db_path=kwargs.get('db_path', 'productos.db')
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
