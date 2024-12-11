import re
from typing import Any, Dict, List, Optional

from sqlmodel import  Session, SQLModel, create_engine, select
from v2.models import Company, JobListing, RawContent

from config.config_class import get_config

config = get_config()

def init_db(url:str=config.db.uri):
    engine = create_engine(url, echo=True)
    SQLModel.metadata.create_all(engine)
    return engine

def store_raw_content(engine, url: str, html: str):
    with Session(engine) as session:
        raw_content = RawContent(url=url, html=html)
        session.add(raw_content)
        session.commit()


def store_extracted_content(engine, job: JobListing):
    with Session(engine) as session:
        session.add(job)
        session.commit()

def get_jobs_by_company(engine, company_name: str):
    with Session(engine) as session:
        statement = select(JobListing).join(Company).where(Company.name == company_name)
        results = session.exec(statement).all()
        return results

engine = init_db()
