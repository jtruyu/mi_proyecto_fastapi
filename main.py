from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import asyncpg
import os
import uvicorn
import json
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

class Usuario(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int

class SimulacroUsuario(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int
    respuestas: str

@app.get("/diagnostico/")
async def get_diagnostico():
    """ Devuelve todos los ejercicios de la tabla ejercicios_admision ordenados por curso """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        orden_cursos = ["RM", "Aritmética", "Algebra", "Geometría", "Trigonometría", "Física", "Química"]
        
        ejercicios = await conn.fetch('SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, curso, tema, dificultad, ciclo FROM "ejercicios_admision"')
        await conn.close()

        if not ejercicios:
            return {"error": "No hay ejercicios en la base de datos"}

        ejercicios_ordenados = sorted(
            ejercicios, 
            key=lambda x: orden_cursos.index(x["curso"]) if x["curso"] in orden_cursos else 999
        )

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
                "curso": p["curso"],
                "tema": p["tema"],
                "dificultad": p["dificultad"],
                "ciclo": p["ciclo"]
            }
            for p in ejercicios_ordenados
        ]

        return preguntas_final

    except Exception as e:
        return {"error": str(e)}

@app.get("/simulacro/")
async def get_simulacro():
    """ Devuelve todos los ejercicios del primer simulacro """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        orden_cursos = ["RM", "RV", "Aritmética", "Algebra", "Geometría", "Trigonometría", "Física", "Química"]
        
        ejercicios = await conn.fetch('SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, curso, tema, dificultad FROM "primer_simulacro"')
        await conn.close()

        if not ejercicios:
            return {"error": "No hay ejercicios en la base de datos"}

        ejercicios_ordenados = sorted(
            ejercicios, 
            key=lambda x: orden_cursos.index(x["curso"]) if x["curso"] in orden_cursos else 999
        )

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
                "curso": p["curso"],
                "tema": p["tema"],
                "dificultad": p["dificultad"]
            }
            for p in ejercicios_ordenados
        ]

        return preguntas_final

    except Exception as e:
        return {"error": str(e)}

@app.post("/guardar-diagnostico")
async def guardar_diagnostico(usuario: Usuario):
    """Guarda los resultados del diagnóstico junto con la información del usuario"""
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
        
        await conn.execute('''
            INSERT INTO resultados_diagnostico
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

@app.post("/guardar-simulacro")
async def guardar_simulacro(usuario: SimulacroUsuario):
    """Guarda los resultados del simulacro junto con la información del usuario"""
    try:
        print("Datos recibidos para simulacro:", usuario.dict())
        
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
        
        # Eliminar el CREATE TABLE IF NOT EXISTS y manejar las respuestas directamente
        await conn.execute('''
            INSERT INTO resultados_simulacro
            (nombre, correo, resultado, preguntas_correctas, preguntas_incorrectas, 
             preguntas_sin_responder, tiempo_usado, respuestas, fecha_realizacion)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
        ''', 
        usuario.nombre, 
        usuario.correo, 
        usuario.resultado, 
        usuario.preguntas_correctas, 
        usuario.preguntas_incorrectas,
        usuario.preguntas_sin_responder,
        usuario.tiempo_usado,
        usuario.respuestas,  # Usar directamente el string JSON
        datetime.now()
        )
        
        await conn.close()
        return {"status": "success", "message": "Resultado de simulacro guardado correctamente"}
    
    except Exception as e:
        print(f"Error en guardar-simulacro: {str(e)}")
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
