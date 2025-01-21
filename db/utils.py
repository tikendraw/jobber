from sqlmodel import SQLModel, create_engine

from config.config_class import get_config

config = get_config()

def init_db(url:str=config.db.uri):
    engine = create_engine(url, echo=True)
    SQLModel.metadata.create_all(engine)
    return engine

# engine = init_db()
