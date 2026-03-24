import os
import sqlite3
import anthropic
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# --- CONFIGURACIÓN DE IA ---
# Pon aquí tu llave de Anthropic (sk-ant...)
client = anthropic.Anthropic(
    api_key='TU_API_KEY_AQUI' 
)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT NOT NULL,
            contenido TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Inicializamos la base de datos
init_db()

@app.route("/")
def home():
    # Esto buscará el archivo index.html dentro de la carpeta /templates
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        # 1. Hablar con la IA (Claude 3.5 Sonnet)
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        bot_response = message.content[0].text

        # 2. Guardar el historial en la base de datos
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mensajes (rol, contenido) VALUES (?, ?)", ("user", user_message))
        cursor.execute("INSERT INTO mensajes (rol, contenido) VALUES (?, ?)", ("assistant", bot_response))
        conn.commit()
        conn.close()

        return jsonify({"response": bot_response})

    except Exception as e:
        # Si hay un error (ej. API Key inválida), lo veremos aquí
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render usa la variable PORT automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
