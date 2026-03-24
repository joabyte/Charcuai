
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import anthropic

app = Flask(__name__)
DB = "charcuteria.db"

# Configuración de Plantillas Automática
def setup_templates():
    if not os.path.exists('templates'): os.makedirs('templates')
    
    # HTML PRINCIPAL (CALENDARIO)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>CharcuAI - Calendario</title>
    <link href="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #fdf5e6; margin: 20px; }
        .container { max-width: 900px; margin: auto; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        h1 { color: #5d4037; text-align: center; border-bottom: 2px solid #d7ccc8; padding-bottom: 10px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { margin: 0 15px; text-decoration: none; color: #8d6e63; font-weight: bold; padding: 5px 10px; border-radius: 5px; background: #efebe9; }
        .form { display: grid; gap: 10px; margin-top: 25px; background: #fafafa; padding: 20px; border-radius: 10px; border: 1px solid #eee; }
        input, button { padding: 12px; border-radius: 6px; border: 1px solid #ddd; }
        button { background: #5d4037; color: white; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background: #3e2723; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🥓 CharcuAI Manager</h1>
        <div class="nav"><a href="/">📅 Calendario</a><a href="/chat">💬 Consultar IA</a></div>
        <div id="calendar"></div>
        <div class="form">
            <h3>Registrar Nuevo Curado</h3>
            <input type="text" id="nombre" placeholder="Nombre del producto (ej: Salame)">
            <input type="date" id="fecha">
            <input type="number" id="dias" placeholder="Días totales de curación">
            <button onclick="guardar()">Añadir Proceso</button>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var calEl = document.getElementById('calendar');
            var calendar = new FullCalendar.Calendar(calEl, {
                initialView: 'dayGridMonth',
                events: '/api/eventos',
                eventClick: function(info) {
                    if(confirm('¿Eliminar ' + info.event.title + '?')) {
                        fetch('/eliminar/'+info.event.id, {method:'DELETE'}).then(() => calendar.refetchEvents());
                    }
                }
            });
            calendar.render();
            window.guardar = function() {
                const data = { nombre: $('#nombre').val(), fecha_inicio: $('#fecha').val(), duracion_dias: $('#dias').val() };
                if(!data.nombre || !data.fecha_inicio) return alert('Faltan datos');
                fetch('/agregar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) })
                .then(() => { calendar.refetchEvents(); alert('Proceso guardado'); });
            };
        });
    </script>
</body>
</html>
''')

    # HTML CHAT (IA)
    with open('templates/chat.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>CharcuAI - Asistente</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { font-family: sans-serif; background: #fdf5e6; padding: 20px; }
        .chat-box { max-width: 600px; margin: auto; background: white; border-radius: 15px; display: flex; flex-direction: column; height: 85vh; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        #messages { flex: 1; overflow-y: auto; padding: 20px; }
        .input-group { display: flex; padding: 15px; border-top: 1px solid #eee; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #5d4037; color: white; border: none; margin-left: 5px; border-radius: 5px; cursor: pointer; }
        .msg { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user { background: #efebe9; text-align: right; }
        .bot { background: #d7ccc8; }
    </style>
</head>
<body>
    <div class="chat-box">
        <div style="text-align:center; padding: 10px;"><a href="/" style="color:#5d4037; text-decoration:none; font-weight:bold;">🔙 Volver al Calendario</a></div>
        <div id="messages"></div>
        <div class="input-group">
            <input type="text" id="p" placeholder="Escribe tu duda sobre charcutería...">
            <button onclick="preguntar()">Preguntar</button>
        </div>
    </div>
    <script>
        function preguntar() {
            const txt = $('#p').val(); if(!txt) return;
            $('#messages').append('<div class="msg user"><b>Tú:</b> '+txt+'</div>');
            $('#p').val('');
            $.ajax({
                url: '/chat', type: 'POST', contentType: 'application/json',
                data: JSON.stringify({pregunta: txt}),
                success: function(res) { $('#messages').append('<div class="msg bot"><b>Claude:</b> '+res.respuesta+'</div>'); }
            });
        }
    </script>
</body>
</html>
''')

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS procesos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, fecha_inicio DATE, duracion_dias INTEGER)")

app = Flask(__name__)

@app.route('/')
def index():
    setup_templates()
    return render_template('index.html')

@app.route('/api/eventos')
def eventos():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM procesos").fetchall()
    res = []
    for r in rows:
        fin = datetime.strptime(r['fecha_inicio'], '%Y-%m-%d') + timedelta(days=int(r['duracion_dias']))
        res.append({'id': r['id'], 'title': r['nombre'], 'start': r['fecha_inicio'], 'end': fin.strftime('%Y-%m-%d')})
    return jsonify(res)

@app.route('/agregar', methods=['POST'])
def agregar():
    d = request.json
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO procesos (nombre, fecha_inicio, duracion_dias) VALUES (?,?,?)", (d['nombre'], d['fecha_inicio'], d['duracion_dias']))
    return jsonify({"status": "ok"})

@app.route('/eliminar/<int:id>', methods=['DELETE'])
def eliminar(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM procesos WHERE id=?", (id,))
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        key = os.environ.get("CLAUDE_API_KEY")
        if not key: return jsonify({"respuesta": "Falta configurar la API KEY en Render."})
        client = anthropic.Anthropic(api_key=key)
        p = request.json.get('pregunta')
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=600,
            messages=[{"role": "user", "content": "Eres un maestro charcutero. Ayuda con esta duda técnica: " + p}]
        )
        return jsonify({"respuesta": msg.content[0].text})
    return render_template('chat.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
