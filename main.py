from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
import random

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    return await asyncpg.connect(DATABASE_URL)

@app.get("/simulacro/{num_preguntas}")
async def get_simulacro(num_preguntas: int):
    conn = await connect_db()

    # Obtener preguntas aleatorias de la tabla Física_prácticas_cepreuni
    ejercicios = await conn.fetch(
        "SELECT Ejercicio, Imagen, A, B, C, D, E, Alt_Correcta, Tema, Subtema, Dificultad FROM Física_prácticas_cepreuni"
    )
    
    preguntas = random.sample(ejercicios, min(num_preguntas, len(ejercicios)))

    await conn.close()

    # Construir la respuesta con las preguntas y alternativas
    preguntas_final = []
    for p in preguntas:
        preguntas_final.append({
            "ejercicio": p["Ejercicio"],
            "imagen": p["Imagen"],  # Puede ser NULL si no hay imagen
            "alternativas": [
                {"letra": "A", "texto": p["A"]},
                {"letra": "B", "texto": p["B"]},
                {"letra": "C", "texto": p["C"]},
                {"letra": "D", "texto": p["D"]},
                {"letra": "E", "texto": p["E"]},
            ],
            "respuesta_correcta": p["Alt_Correcta"],  # Letra de la alternativa correcta
            "tema": p["Tema"],
            "subtema": p["Subtema"],
            "dificultad": p["Dificultad"]
        })

    return preguntas_final


class RespuestaInput(BaseModel):
    estudiante_id: int
    ejercicio: str  # Ahora se usa el enunciado en vez del ID
    alternativa_seleccionada: str  # Letra de la respuesta elegida (A, B, C, D, E)

@app.post("/responder")
async def responder(respuesta: RespuestaInput):
    conn = await connect_db()
    try:
        await conn.execute(
            "INSERT INTO respuestas (estudiante_id, ejercicio, alternativa_seleccionada) VALUES ($1, $2, $3)",
            respuesta.estudiante_id, respuesta.ejercicio, respuesta.alternativa_seleccionada
        )
        return {"mensaje": "Respuesta guardada con éxito"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()

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
