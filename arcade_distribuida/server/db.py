from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Motor SQLite. El archivo de base de datos se llamará resultados.db en la raíz del proyecto.
engine = create_engine('sqlite:///resultados.db', echo=True)

# Fábrica de sesiones
Session = sessionmaker(bind=engine)

# Clase base para los modelos ORM
Base = declarative_base()

def init_db():
    """
    Crea todas las tablas definidas en los modelos si no existen.
    Llama a Base.metadata.create_all sobre el engine.
    """
    Base.metadata.create_all(engine)
