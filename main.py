import os
import json
import uuid
from io import BytesIO
from datetime import datetime, timezone
from groq import Groq
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage


def main(context):
    try:
        # === Configuración desde .env ===
        groq_key = os.environ.get("GROQ_API_KEY")
        aw_endpoint = os.environ.get("APPWRITE_FUNCTION_API_ENDPOINT")
        aw_project = os.environ.get("APPWRITE_FUNCTION_PROJECT_ID")
        aw_key = os.environ.get("APPWRITE_FUNCTION_API_KEY")

        # Variables que antes estaban hardcodeadas
        bucket_id = os.environ.get("BUCKET_ID", "TU_BUCKET_ID_AQUI")
        database_id = os.environ.get("DATABASE_ID", "TU_DATABASE_ID_AQUI")
        collection_id = os.environ.get("COLLECTION_ID", "TU_COLLECTION_ID_AQUI")
        transcription_model = os.environ.get("TRANSCRIPTION_MODEL", "whisper-large-v3")
        translation_model = os.environ.get("TRANSLATION_MODEL", "llama-3.3-70b-versatile")

        print("🔹 Variables de entorno:")
        print(f"GROQ_API_KEY: {'✅' if groq_key else '❌'}")
        print(f"APPWRITE_FUNCTION_API_ENDPOINT: {aw_endpoint}")
        print(f"APPWRITE_FUNCTION_PROJECT_ID: {aw_project}")
        print(f"APPWRITE_FUNCTION_API_KEY: {'✅' if aw_key else '❌'}")
        print(f"BUCKET_ID: {bucket_id}")
        print(f"DATABASE_ID: {database_id}")
        print(f"COLLECTION_ID: {collection_id}")
        print(f"TRANSCRIPTION_MODEL: {transcription_model}")
        print(f"TRANSLATION_MODEL: {translation_model}")

        if not (groq_key and aw_endpoint and aw_project and aw_key):
            return context.res.json({"error": "Faltan variables de entorno críticas"}, 500)

        # === Inicializar clientes ===
        groq_client = Groq(api_key=groq_key)

        aw_client = Client()
        aw_client.set_endpoint(aw_endpoint)
        aw_client.set_project(aw_project)
        aw_client.set_key(aw_key)

        databases = Databases(aw_client)
        storage = Storage(aw_client)

        # === Leer cuerpo ===
        body_raw = context.req.body_raw or "{}"
        print("📥 Body recibido:")
        print(body_raw)

        try:
            body = json.loads(body_raw)
        except Exception as e:
            print("⚠️ Error al parsear JSON:", e)
            return context.res.json({"error": "Cuerpo inválido, debe ser JSON"}, 400)

        # === Extraer campos ===
        file_id = body.get("file_id")
        tipo_input = body.get("tipo", "es")
        user_id = body.get("user_id", "anonimo")

        print(f"📌 file_id={file_id}, tipo={tipo_input}, user_id={user_id}")

        if not file_id:
            return context.res.json({"error": "No se envió file_id"}, 400)

        # === Descargar archivo desde Storage ===
        try:
            file_data = storage.get_file_download(bucket_id, file_id)
            audio_bytes = file_data
        except Exception as e:
            print("❌ Error al descargar archivo:", str(e))
            return context.res.json({
                "error": "No se pudo descargar el archivo desde Storage",
                "detalle": str(e)
            }, 500)

        temp_path = f"/tmp/{uuid.uuid4()}.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        print(f"✅ Archivo descargado y guardado en {temp_path}")

        # === Transcripción ===
        with open(temp_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_path, f.read()),
                model=transcription_model,
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
                model=translation_model
            )
            translation_text = translation.choices[0].message.content.strip()

        # === Limpiar archivo temporal ===
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("🧹 Archivo temporal eliminado.")

        # === Eliminar archivo del Storage ===
        try:
            storage.delete_file(bucket_id, file_id)
            print(f"🗑️ Archivo {file_id} eliminado del bucket {bucket_id}.")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar el archivo {file_id} del Storage: {str(e)}")

        # === Guardar en Appwrite ===
        tipo_registro = "transcripcion" if tipo_input == "es" else "traduccion"
        databases.create_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id="unique()",
            data={
                "user_id": user_id,
                "tipo": tipo_registro,
                "idioma": tipo_input,
                "fecha_hora": datetime.now(timezone.utc).isoformat()
            }
        )

        # === Respuesta final ===
        return context.res.json({
            "success": True,
            "tipo": tipo_registro,
            "idioma": tipo_input,
            "transcription": transcription_text,
            "translation": translation_text
        })

    except Exception as e:
        print("❌ Error en main:", str(e))
        return context.res.json({"success": False, "error": str(e)}, 500)
