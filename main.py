from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
import random

app = FastAPI()  # 📌 Definir app antes de cualquier ruta

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    return await asyncpg.connect(DATABASE_URL)
@app.get("/simulacro/{num_preguntas}")
async def get_simulacro(num_preguntas: int):
    conn = await connect_db()
    
    # Obtener preguntas aleatorias con su respuesta correcta
    ejercicios = await conn.fetch(
        "SELECT id, tema_id, enunciado, nivel_dificultad, respuesta_correcta FROM ejercicios"
    )
    preguntas = random.sample(ejercicios, min(num_preguntas, len(ejercicios)))
    
    # Obtener IDs de preguntas seleccionadas
    ids_preguntas = [p["id"] for p in preguntas]
    
    # Obtener alternativas de las preguntas seleccionadas
    query = "SELECT ejercicio_id, letra, texto FROM alternativas WHERE ejercicio_id = ANY($1)"
    alternativas = await conn.fetch(query, ids_preguntas)
    
    await conn.close()

    # Organizar alternativas por pregunta
    alternativas_dict = {p["id"]: [] for p in preguntas}
    for alt in alternativas:
        alternativas_dict[alt["ejercicio_id"]].append({"letra": alt["letra"], "texto": alt["texto"]})

    # Construir respuesta final con preguntas y sus alternativas
    preguntas_final = []
    for p in preguntas:
        preguntas_final.append({
            "id": p["id"],
            "tema_id": p["tema_id"],
            "enunciado": p["enunciado"],
            "nivel_dificultad": p["nivel_dificultad"],
            "respuesta_correcta": p["respuesta_correcta"],  # ✅ Se agrega la respuesta correcta
            "alternativas": alternativas_dict[p["id"]]
        })

    return preguntas_final


from pydantic import BaseModel

class RespuestaInput(BaseModel):
    estudiante_id: int
    ejercicio_id: int
    alternativa_id: int

@app.post("/responder")
async def responder(respuesta: RespuestaInput):
    conn = await connect_db()
    try:
        await conn.execute(
            "INSERT INTO respuestas (estudiante_id, ejercicio_id, alternativa_id) VALUES ($1, $2, $3)",
            respuesta.estudiante_id, respuesta.ejercicio_id, respuesta.alternativa_id
        )
        return {"mensaje": "Respuesta guardada con éxito"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()
        
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes cambiar "*" por ["http://localhost:3000"] para mayor seguridad
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)






