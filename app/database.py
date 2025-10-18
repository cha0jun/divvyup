## db config for sqlite3
from fastapi import Depends
from sqlmodel import Session, create_engine
from typing import Annotated
from pathlib import Path
import mysql.connector
import os

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_DRIVER = os.environ.get("DB_DRIVER", "pymysql")

try:
    mydb = mysql.connector.connect(
      host=DB_HOST,
      user=DB_USER,
      password=DB_PASSWORD,
      database=DB_NAME
    )
    print("Successfully connected to the database.")
    # You can now create a cursor and execute queries
    # cursor = mydb.cursor()
    # ...

except mysql.connector.Error as err:
    print(f"Error: {err}")

'''
# 1. Get the path to the current file (e.g., .../project-folder/app/database.py)
current_file_path = Path(__file__).resolve()

# 2. Get the path to the 'app' directory (.../project-folder/app)
app_dir = current_file_path.parent

# 3. Get the path to the project's root directory (.../project-folder)
PROJECT_ROOT = app_dir.parent

# 4. Construct the final, absolute path to your database file
DATABASE_PATH = PROJECT_ROOT / "data" / "app.db"

# Ensure data folder exists. May added this line to temporarily fix missing folder error. Remove if you don't face the same issue.
# DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# 5. Create the database URL with the absolute path
DATABASE_URL = f"mysql:///{DATABASE_PATH}"

#May added connect_args={"check_same_thread": False}
# engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
engine = create_engine(DATABASE_URL, echo=False)
'''

DATABASE_URL = f"mysql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)

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


