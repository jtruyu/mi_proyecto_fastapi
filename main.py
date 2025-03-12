from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
import random
import re

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    return await asyncpg.connect(DATABASE_URL)

def format_math(text):
    """Convierte expresiones LaTeX en formato $$...$$"""
    return re.sub(r'\\\((.*?)\\\)', r'$$\1$$', text)

@app.get("/simulacro/{num_preguntas}")
async def get_simulacro(num_preguntas: int):
    async with await connect_db() as conn:  # Se usa async with para manejar mejor la conexión
        try:
            # Obtener preguntas aleatorias
            ejercicios = await conn.fetch(
                'SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, tema, subtema, dificultad FROM "física_prácticas_cepreuni"'
            )

            preguntas = random.sample(ejercicios, min(num_preguntas, len(ejercicios)))

            # Construir respuesta con las preguntas formateadas
            preguntas_final = []
            for p in preguntas:
                preguntas_final.append({
                    "ejercicio": format_math(p["ejercicio"]),  # Asegura el formato $$ $$ en las ecuaciones
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
                })

            return preguntas_final
        except Exception as e:
            return {"error": str(e)}

class RespuestaInput(BaseModel):
    estudiante_id: int
    ejercicio: str
    alternativa_seleccionada: str  # Letra de la respuesta elegida (A, B, C, D, E)

@app.post("/responder")
async def responder(respuesta: RespuestaInput):
    async with await connect_db() as conn:
        try:
            await conn.execute(
                'INSERT INTO respuestas (estudiante_id, ejercicio, alternativa_seleccionada) VALUES ($1, $2, $3)',
                respuesta.estudiante_id, respuesta.ejercicio, respuesta.alternativa_seleccionada
            )
            return {"mensaje": "Respuesta guardada con éxito"}
        except Exception as e:
            return {"error": str(e)}

# Configurar CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
