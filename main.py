@app.get("/simulacro/{num_preguntas}")
async def get_simulacro(num_preguntas: int):
    try:
        conn = await connect_db()  # Establecer conexión
        try:
            ejercicios = await conn.fetch(
                'SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, tema, subtema, dificultad FROM "física_prácticas_cepreuni"'
            )
        finally:
            await conn.close()  # Cerrar conexión al finalizar
        
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
