import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <div style='text-align:center; padding:50px; font-family:sans-serif;'>
        <h1 style='color:#6d6dff;'>CharcuAI Activo ✅</h1>
        <p style='font-size:1.2em;'>Si estás viendo esto, tu app en Render está funcionando perfectamente.</p>
        <hr style='width:50%; margin: 20px auto;'>
        <p style='color:gray;'>Próximo paso: Conectar con Anthropic.</p>
    </div>
    """

if __name__ == "__main__":
    # Render asigna un puerto dinámico, lo leemos de la variable PORT
    # Si no existe (local), usamos el 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
