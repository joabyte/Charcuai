
import os, sqlite3, anthropic
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
@app.route("/")
def home(): return "<h1>CharcuAI Activo</h1><p>Si ves esto, Render funciona!</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
