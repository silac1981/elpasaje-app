from app.db.base_class import Base

# Importar TODOS los modelos para que Alembic los detecte
from app.models.tenant import Tenant
from app.models.client import Client
from app.models.product import Product
