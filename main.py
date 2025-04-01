from fastapi import FastAPI, Query
from pydantic import BaseModel
import asyncpg
import random
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

preguntas_mostradas = {}  # Diccionario para almacenar las preguntas ya vistas por usuario

async def connect_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

@app.get("/siguiente_pregunta/{user_id}")
async def siguiente_pregunta(user_id: str, temas: list[str] = Query([])):
    """ Devuelve una nueva pregunta sin repetir dentro de una sesión del usuario """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        query = 'SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, tema, subtema, dificultad FROM "física_prácticas_cepreuni"'
        
        if temas:
            temas_str = "', '".join(temas)
            query += f" WHERE tema IN ('{temas_str}')"

        ejercicios = await conn.fetch(query)
        await conn.close()

        if not ejercicios:
            return {"error": "No hay ejercicios en la base de datos para los temas seleccionados"}

        # Inicializar el historial si el usuario no existe en el diccionario
        if user_id not in preguntas_mostradas:
            preguntas_mostradas[user_id] = set()

        # Filtrar ejercicios no mostrados
        preguntas_disponibles = [p for p in ejercicios if p["ejercicio"] not in preguntas_mostradas[user_id]]

        # Si ya se mostraron todas, resetear la lista
        if not preguntas_disponibles:
            preguntas_mostradas[user_id] = set()
            preguntas_disponibles = ejercicios

        # Seleccionar una pregunta al azar
        pregunta = random.choice(preguntas_disponibles)
        preguntas_mostradas[user_id].add(pregunta["ejercicio"])

        return {
            "ejercicio": pregunta["ejercicio"],
            "imagen": pregunta["imagen"],
            "alternativas": [
                {"letra": "A", "texto": pregunta["a"]},
                {"letra": "B", "texto": pregunta["b"]},
                {"letra": "C", "texto": pregunta["c"]},
                {"letra": "D", "texto": pregunta["d"]},
                {"letra": "E", "texto": pregunta["e"]},
            ],
            "respuesta_correcta": pregunta["alt_correcta"],
            "tema": pregunta["tema"],
            "subtema": pregunta["subtema"],
            "dificultad": pregunta["dificultad"]
        }

    except Exception as e:
        return {"error": str(e)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  
    uvicorn.run(app, host="0.0.0.0", port=port)
