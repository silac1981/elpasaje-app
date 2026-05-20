"""utils/db.py — motor SQLAlchemy compartido por todos los módulos."""
import os
from sqlalchemy import create_engine

# El archivo .db vive en la raíz del repo, un nivel arriba de utils/
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elpasaje_v2.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
