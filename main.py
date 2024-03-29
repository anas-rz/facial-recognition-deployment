from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector
from deepface import DeepFace
from PIL import Image
import io
import os

app = FastAPI()

# Database configuration
DB_NAME = 'embeddings_db'
DB_USER = 'anas'
DB_PASSWORD = 'dba'
DB_HOST = os.environ['DB_HOST']

# Connect to database and register vector support
conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port='5432')
cursor = conn.cursor()
cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
register_vector(conn)
# Create embeddings table if it doesn't exist
#cursor.execute("CREATE EXTENSION vector;")
cursor.execute('CREATE TABLE IF NOT EXISTS facial_embeddings (id bigserial PRIMARY KEY, name VARCHAR(4096), embedding vector(4096))')
#cursor.execute('CREATE INDEX IF NOT EXISTS facial_embeddings_idx ON facial_embeddings USING hnsw (embedding vector_l2_ops)')

# Routes
@app.post('/embeddings')
async def add_embeddings(file: UploadFile = File(...), name: str = Form('')):
    try:
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes))
        img = np.array(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        embeddings = DeepFace.represent(img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    embedding_vector = np.array(embeddings[0]['embedding'])
    cursor.execute('INSERT INTO facial_embeddings (name, embedding) VALUES (%s, %s)', (name, embedding_vector))
    conn.commit()

    return {'message': 'Embeddings added successfully'}

@app.post('/embeddings/closest')
async def get_closest_embeddings(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes))
        img = np.array(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        target_embeddings = DeepFace.represent(img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    target_embedding_vector = np.array(target_embeddings[0]['embedding'])
    cursor.execute('SELECT * FROM facial_embeddings ORDER BY embedding <-> %s LIMIT 3', (target_embedding_vector,))
    closest_embeddings = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    return closest_embeddings

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

