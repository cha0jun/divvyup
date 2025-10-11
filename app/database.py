## db config for sqlite3
from fastapi import Depends
from sqlmodel import Session, create_engine
from typing import Annotated

db_path = "../data/app.db" # hardcoded relative path as db is on the same server as app
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo =False)

def get_session():
    with Session(engine) as session:
        yield session
# handles sessions between app and db
SessionDep = Annotated[Session, Depends(get_session)]

'''
sample usage
@router.get("/items/{item_id}")
def read_item(item_id: int, db: SessionDep): # <-- Clean and concise
    return crud.get_item(db=db, item_id=item_id)
'''


