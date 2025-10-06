import os
import json
import uuid
from datetime import datetime
from groq import Groq
from appwrite.client import Client
from appwrite.services.databases import Databases

def main(context):
    try:
        # === Configuración ===
        groq_key = os.environ.get("GROQ_API_KEY")
        aw_endpoint = os.environ.get("APPWRITE_FUNCTION_API_ENDPOINT")
        aw_project = os.environ.get("APPWRITE_FUNCTION_PROJECT_ID")
        aw_key = os.environ.get("APPWRITE_FUNCTION_API_KEY")

        if not (groq_key and aw_endpoint and aw_project and aw_key):
            return context.res.json({"error": "Faltan variables de entorno"}, 500)

        # === Inicializar Groq y Appwrite ===
        groq_client = Groq(api_key=groq_key)
        aw_client = Client()
        aw_client.set_endpoint(aw_endpoint)
        aw_client.set_project(aw_project)
        aw_client.set_key(aw_key)
        databases = Databases(aw_client)

        # === Leer datos ===
        files = context.req.files or {}
        body = json.loads(context.req.body_raw or "{}")
        tipo_input = body.get("tipo", "es")  # "es" (solo transcripción) o "en" (transcripción+traducción)
        user_id = body.get("user_id", "anonimo")

        if "audio" not in files:
            return context.res.json({"error": "No se proporcionó archivo de audio"}, 400)

        audio = files["audio"]
        filename = audio["filename"]
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in {"wav", "mp3", "m4a", "ogg"}:
            return context.res.json({"error": f"Tipo de archivo no soportado: .{ext}"}, 400)

        # === Guardar temporalmente ===
        temp_path = f"/tmp/{uuid.uuid4()}.{ext}"
        with open(temp_path, "wb") as f:
            f.write(audio["data"])

        # === Transcripción ===
        with open(temp_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_path, f.read()),
                model="whisper-large-v3",
                response_format="json",
                language="es" if tipo_input == "es" else "en",
                temperature=0.0
            )
        transcription_text = transcription.text.strip()

        # === Traducción si es inglés ===
        translation_text = None
        if tipo_input == "en":
            translation = groq_client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": f"Traduce al español el siguiente texto: {transcription_text}"
                }],
                model="llama-3.3-70b-versatile"
            )
            translation_text = translation.choices[0].message.content.strip()

        # === Limpiar archivo temporal ===
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # === Guardar solo los campos que existen en la colección ===
        tipo_registro = "transcripcion" if tipo_input == "es" else "traduccion"
        databases.create_document(
            database_id="babel_db",
            collection_id="historial",
            document_id="unique()",
            data={
                "user_id": user_id,
                "tipo": tipo_registro,
                "idioma": tipo_input,
                "fecha_hora": datetime.now().isoformat()
            }
        )

        # === Respuesta al front ===
        response = {
            "success": True,
            "tipo": tipo_registro,
            "idioma": tipo_input,
            "transcription": transcription_text,
            "translation": translation_text
        }

        return context.res.json(response)

    except Exception as e:
        return context.res.json({"success": False, "error": str(e)}, 500)
