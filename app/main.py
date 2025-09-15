from fastapi import FastAPI, Request, HTTPException
import os

#3
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()
DATA_FILE = "/data/notas.txt"


#2
AUTOR = os.getenv("AUTOR", "Autor no configurado")

#3
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

#3
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None


#2
@app.get("/autor")
def obtener_autor():
    return {"autor": AUTOR}


@app.post("/notas")
async def guardar_nota(request: Request):
    nota = await request.body()
    with open(DATA_FILE, "a") as f:
        f.write(nota.decode() + "\n")

    #3
    if all([DB_HOST, DB_USER, DB_PASS, DB_NAME]):
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO notas (contenido) VALUES (%s) RETURNING id",
                        (nota.decode(),)
                    )
                    conn.commit()
                    print(f"Nota guardada en BD con ID: {cur.fetchone()['id']}")
            except Exception as e:
                print(f"Error insertando en la base de datos: {e}")
            finally:
                conn.close()
    
    return {"mensaje": "Nota guardada"}
    

    
@app.get("/conteo")
def contar_notas():
    if not os.path.exists(DATA_FILE):
        return {"conteo": 0}
    with open(DATA_FILE, "r") as f:
        return {"conteo": sum(1 for _ in f)}

@app.get("/")
def leer_nota():
    if not os.path.exists(DATA_FILE):
        return {"notas": []}
    with open(DATA_FILE, "r") as f:
        return {"notas": f.read().splitlines()}


#3
@app.get("/notas-db")
def leer_notas_db():
    if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME]):
        raise HTTPException(status_code=500, detail="Base de datos no configurada")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, contenido FROM notas ORDER BY id")
            notas = cur.fetchall()
        return {"notas_db": notas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando la base de datos: {str(e)}")
    finally:
        conn.close()