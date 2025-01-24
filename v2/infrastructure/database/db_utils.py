# infrastructure/database/db_utils.py
from typing import Any, Dict, List, Optional

# from infrastructure.database.models import RawContent
from sqlmodel import Session, SQLModel, create_engine, select

# from v2.config.config_loader import get_config
from v2.infrastructure.database.base_model import BaseModel
# 
# config, _ = get_config()



def init_db(url:str=None):
    if url:
        engine = create_engine(url, echo=True)
        SQLModel.metadata.create_all(engine)
        return engine

def store_raw_content(engine:Any, url: str, html: str, model: type[BaseModel] = None):
    with Session(engine) as session:
        raw_content = model(url=url, html=html)
        session.add(raw_content)
        session.commit()

def store_extracted_content(engine:Any, job: BaseModel, model:type[BaseModel] = None):
    with Session(engine) as session:
        session.add(job)
        session.commit()

def get_items_by_name(engine:Any, table:type[SQLModel], name: str, model:type[BaseModel] = None):
    with Session(engine) as session:
        statement = select(table).where(table.name == name)
        results = session.exec(statement).all()
        return results
    
# engine = init_db()
