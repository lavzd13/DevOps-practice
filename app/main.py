import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

app = FastAPI()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    db_host: str
    db_name: str
    db_role: str
    db_password: str

class Note(BaseModel):
    text: str

settings = Settings()

def open_connection():
    connection = psycopg2.connect(
          database=settings.db_name,
          user=settings.db_role,
          password=settings.db_password,
          host=settings.db_host
    )
    return connection

# This function will return note from DB
@app.get("/notes/{note_id}")
def read_note(note_id: int):
    connection = open_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT notes_id, text, created_at FROM notes WHERE notes_id = %s", (note_id,))
    data = cursor.fetchone()
    connection.close()
    if data is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"note_id": data[0], "text": data[1], "created_at": data[2]}

# This function checks if our process is alive
@app.get("/healthz")
def check_status():
    pass

# This function checks if our DB is operational
@app.get("/readyz")
def check_db():
    try:
        connection = open_connection()
        connection.close()
    except psycopg2.OperationalError:
        raise HTTPException(status_code=500, detail="Internal server error")

# This function will create new note in our DB
@app.post("/notes")
def create_note(note: Note):
    connection = open_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO notes (text) VALUES (%s) RETURNING notes_id", (note.text,))
    data = cursor.fetchone()
    connection.commit()
    connection.close()
    return {"notes_id": data[0]}