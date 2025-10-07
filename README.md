# BabelSpeak Functions

Esta carpeta contiene la función de Appwrite para **transcripción y traducción de audio** usando Groq, junto con el registro de historial en Appwrite y manejo de archivos temporales en un bucket de Storage.

---

## Estructura de la carpeta

```
babel-functions/
│
├─ main.py              # Función principal para Appwrite
├─ requirements.txt     # Dependencias de Python
├─ .env.example         # Variables de entorno de ejemplo
└─ README.md            # Este archivo
```

---

## Requisitos

- Python 3.13+
- Pip
- Cuenta Appwrite configurada
- API Key de Groq

---

## Configuración

1. Copia `.env.example` a `.env`:

```bash
cp .env.example .env
```

2. Rellena las variables:

```env
GROQ_API_KEY=TU_GROQ_API_KEY_AQUI
APPWRITE_FUNCTION_API_ENDPOINT=TU_APPWRITE_ENDPOINT_AQUI
APPWRITE_FUNCTION_PROJECT_ID=TU_PROJECT_ID_AQUI
APPWRITE_FUNCTION_API_KEY=TU_FUNCTION_API_KEY_AQUI

# Storage & DB
BUCKET_ID=TU_BUCKET_ID_AQUI
DATABASE_ID=TU_DATABASE_ID_AQUI
COLLECTION_ID=TU_COLLECTION_ID_AQUI

# Modelos Groq
TRANSCRIPTION_MODEL=whisper-large-v3
TRANSLATION_MODEL=llama-3.3-70b-versatile
```

> Nota: reemplaza todos los valores por tus propios IDs y claves.

---

## Instalación de dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**

```
appwrite==13.2.0
groq==0.31.0
python-multipart==0.0.20
```

---

## Uso

### En Appwrite

1. Sube la carpeta `babel-functions/` como función de Appwrite.
2. Configura las variables de entorno en la interfaz de Appwrite.
3. Llama a la función desde tu frontend pasando:

```json
{
  "file_id": "ID_DEL_ARCHIVO_SUBIDO_AL_BUCKET",
  "tipo": "es",       # "es" = solo transcripción, "en" = transcripción + traducción
  "user_id": "usuario123"
}
```

- La función descargará el archivo desde el bucket configurado, lo transcribirá, traducirá si corresponde y luego lo eliminará del bucket.
- Se guardará un registro en Appwrite con `user_id`, `tipo`, `idioma` y `fecha_hora`.
- La transcripción (`transcription`) y la traducción (`translation`) se devuelven en la respuesta pero **no se guardan** en la base de datos.

---

### Localmente (opcional)

```bash
export $(cat .env | xargs)  # Linux/macOS
# o en Windows PowerShell:
# setx VAR_NAME "value"
python main.py
```

> Para pruebas locales, necesitarías adaptar `main.py` a un servidor Flask u otra interfaz HTTP.

---

## Notas

- `tipo`: `"es"` = transcripción, `"en"` = transcripción + traducción.
- Los archivos se eliminan automáticamente del bucket tras procesarse.
- Los modelos de Groq se pueden configurar desde `.env`.
- Mantén las variables de entorno seguras y no compartas tus claves ni IDs reales.
