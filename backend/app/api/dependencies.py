from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.app.db import SessionFactory


def get_session():
    with SessionFactory() as session:
        try:
            yield session
        finally:
            session.rollback()


@lru_cache
def get_storage():
    from backend.app.config import get_settings
    from backend.app.storage.local import LocalStorage
    return LocalStorage(get_settings().storage_root)


DB = Annotated[Session, Depends(get_session)]
