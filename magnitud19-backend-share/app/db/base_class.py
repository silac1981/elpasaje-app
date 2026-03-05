from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Naming convention: hace que Alembic genere nombres para FKs/IX/UK/etc.
# Esto es CLAVE para SQLite + batch mode (si no, rompe con "Constraint must have a name")
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata
