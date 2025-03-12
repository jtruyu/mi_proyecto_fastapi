from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
import random
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None  # Manejo explícito del error

@app.get("/simulacro/{num_preguntas}")
async def get_simulacro(num_preguntas: int):
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        try:
            ejercicios = await conn.fetch(
                'SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, tema, subtema, dificultad FROM "física_prácticas_cepreuni"'
            )
        finally:
            await conn.close()  # Cierra la conexión correctamente

        if not ejercicios:
            return {"error": "No hay ejercicios en la base de datos"}

        preguntas = random.choices(ejercicios, k=min(num_preguntas, len(ejercicios)))

        preguntas_final = [
            {
                "ejercicio": p["ejercicio"],
                "imagen": p["imagen"],
                "alternativas": [
                    {"letra": "A", "texto": p["a"]},
                    {"letra": "B", "texto": p["b"]},
                    {"letra": "C", "texto": p["c"]},
                    {"letra": "D", "texto": p["d"]},
                    {"letra": "E", "texto": p["e"]},
                ],
                "respuesta_correcta": p["alt_correcta"],
                "tema": p["tema"],
                "subtema": p["subtema"],
                "dificultad": p["dificultad"]
            }
            for p in preguntas
        ]

        return preguntas_final

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
