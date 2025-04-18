from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import asyncpg
import random
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Modelo para recibir los datos del usuario
class Usuario(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int

@app.get("/temas")
async def get_temas():
    """ Devuelve una lista de los temas disponibles en la base de datos """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        temas = await conn.fetch('SELECT DISTINCT tema FROM "física_prácticas_cepreuni"')
        await conn.close()
        
        return [t["tema"] for t in temas]
    except Exception as e:
        return {"error": str(e)}

@app.get("/simulacro/")
async def get_simulacro(num_preguntas: int = 10, temas: list[str] = Query([])):
    """ Devuelve preguntas filtradas por los temas seleccionados sin repetir """
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

        # Evitar preguntas repetidas
        if len(ejercicios) < num_preguntas:
            return {"error": "No hay suficientes preguntas para mostrar"}

        # Elegir aleatoriamente las preguntas sin repetirse
        preguntas = random.sample(ejercicios, num_preguntas)

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

@app.post("/guardar-resultado")
async def guardar_resultado(usuario: Usuario):
    """Guarda los resultados del simulacro junto con la información del usuario"""
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
        
        # Crear la tabla si no existe
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS resultados_simulacro (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                correo TEXT,
                resultado FLOAT,
                preguntas_correctas INTEGER,
                preguntas_incorrectas INTEGER,
                preguntas_sin_responder INTEGER,
                tiempo_usado INTEGER,
                fecha_realizacion TIMESTAMP
            )
        ''')
        
        # Insertar los datos del resultado
        await conn.execute('''
            INSERT INTO resultados_simulacro
            (nombre, correo, resultado, preguntas_correctas, preguntas_incorrectas, preguntas_sin_responder, tiempo_usado, fecha_realizacion)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', 
        usuario.nombre, 
        usuario.correo, 
        usuario.resultado, 
        usuario.preguntas_correctas, 
        usuario.preguntas_incorrectas,
        usuario.preguntas_sin_responder,
        usuario.tiempo_usado,
        datetime.now()
        )
        
        await conn.close()
        return {"status": "success", "message": "Resultado guardado correctamente"}
    
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
