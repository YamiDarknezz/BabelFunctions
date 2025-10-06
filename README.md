# BabelSpeak Functions

Esta carpeta contiene la función de Appwrite para **transcripción y traducción de audio** usando Groq, junto con el registro de historial en Appwrite.

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

```
GROQ_API_KEY=your_groq_api_key_here
APPWRITE_FUNCTION_API_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_FUNCTION_PROJECT_ID=your_project_id
APPWRITE_FUNCTION_API_KEY=your_function_api_key
PORT=5000   # Opcional si se prueba localmente
```

---

## Instalación de dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**

```
groq==0.31.0
appwrite==13.2.0
```

---

## Uso

### En Appwrite

1. Sube la carpeta `babel-functions/` como función de Appwrite.
2. Configura las variables de entorno en la interfaz de Appwrite.
3. Llama a la función desde tu frontend pasando:

```json
{
  "tipo": "es",  # "es" = solo transcripción, "en" = transcripción + traducción
  "user_id": "usuario123"
}
```

y el archivo de audio en `multipart/form-data` bajo la clave `audio`.

---

### Localmente (opcional)

```bash
export $(cat .env | xargs)  # Linux/macOS
# o en Windows PowerShell:
# setx VAR_NAME "value"
python main.py
```

Esto levantará un servidor local (si adaptas main.py a Flask para pruebas).

---

## Notas

- La función **guarda solo** los campos definidos en la colección `historial` de Appwrite: `user_id`, `tipo`, `idioma`, `fecha_hora`.
- `transcription` y `translation` se envían en la respuesta, pero **no se guardan** en la base de datos.
- `tipo`: `"es"` = transcripción, `"en"` = transcripción + traducción.
