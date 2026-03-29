import os
import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ================= CONFIGURACIÓN =================
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# ================= DATOS DE MEDICINA CHINA =================
TCM_DATA = {
    "elementos": [
        {"nombre": "Madera", "organos": "Hígado, Vesícula Biliar", "emocion": "Ira", "estacion": "Primavera", "sabor": "Ácido"},
        {"nombre": "Fuego", "organos": "Corazón, Intestino Delgado", "emocion": "Alegría", "estacion": "Verano", "sabor": "Amargo"},
        {"nombre": "Tierra", "organos": "Bazo, Estómago", "emocion": "Preocupación", "estacion": "Cambio de estación", "sabor": "Dulce"},
        {"nombre": "Metal", "organos": "Pulmón, Intestino Grueso", "emocion": "Tristeza", "estacion": "Otoño", "sabor": "Picante"},
        {"nombre": "Agua", "organos": "Riñón, Vejiga", "emocion": "Miedo", "estacion": "Invierno", "sabor": "Salado"}
    ],
    "dietas": [
        {"nombre": "Jengibre", "naturaleza": "Caliente", "uso": "Dispela el frío, mejora digestión", "recomendado_para": "Frío interno, náuseas"},
        {"nombre": "Pepino", "naturaleza": "Fresco", "uso": "Refresca, elimina calor", "recomendado_para": "Calor interno, sed"},
        {"nombre": "Arroz integral", "naturaleza": "Neutro", "uso": "Fortalece el Bazo", "recomendado_para": "Fatiga, digestión débil"},
        {"nombre": "Canela", "naturaleza": "Caliente", "uso": "Calienta los riñones", "recomendado_para": "Frío en extremidades"},
        {"nombre": "Menta", "naturaleza": "Fresca", "uso": "Dispela el viento-calor", "recomendado_para": "Resfriados con fiebre"},
        {"nombre": "Sésamo negro", "naturaleza": "Neutro", "uso": "Nutre la sangre", "recomendado_para": "Vértigo, cabello frágil"},
        {"nombre": "Pollo", "naturaleza": "Templada", "uso": "Tonifica el Qi", "recomendado_para": "Debilidad general"},
        {"nombre": "Tofu", "naturaleza": "Fresco", "uso": "Humedece sequedad", "recomendado_para": "Sequedad de piel"},
        {"nombre": "Cúrcuma", "naturaleza": "Caliente", "uso": "Activa circulación", "recomendado_para": "Dolor estancado"},
        {"nombre": "Manzana", "naturaleza": "Neutra", "uso": "Armoniza el estómago", "recomendado_para": "Digestión lenta"}
    ],
    "puntos_acupuntura": [
        {"nombre": "LI4 (Hegu)", "ubicacion": "Dorso de la mano, entre 1° y 2° metacarpiano", "indicaciones": "Dolor de cabeza, resfriados, analgesia", "precio_sugerido": "$15 - $25"},
        {"nombre": "ST36 (Zusanli)", "ubicacion": "4 dedos debajo de la rótula, lateral", "indicaciones": "Fortalece digestión, energía", "precio_sugerido": "$20 - $30"},
        {"nombre": "SP6 (Sanyinjiao)", "ubicacion": "3 dedos arriba del maléolo interno", "indicaciones": "Problemas ginecológicos, insomnio", "precio_sugerido": "$20 - $30"},
        {"nombre": "PC6 (Neiguan)", "ubicacion": "2 dedos arriba de la muñeca, entre tendones", "indicaciones": "Náuseas, ansiedad, palpitaciones", "precio_sugerido": "$15 - $25"},
        {"nombre": "GV20 (Baihui)", "ubicacion": "Vértice de la cabeza", "indicaciones": "Cefalea, vértigo, prolapso", "precio_sugerido": "$10 - $20"},
        {"nombre": "BL23 (Shenshu)", "ubicacion": "Espalda, a nivel de L2, 1.5 cun lateral", "indicaciones": "Lumbago, debilidad renal", "precio_sugerido": "$20 - $30"},
        {"nombre": "LU7 (Lieque)", "ubicacion": "Muñeca, sobre la apófisis estiloides radial", "indicaciones": "Tos, dolor de cuello", "precio_sugerido": "$15 - $25"}
    ],
    "precios": {
        "consulta_inicial": "$60 - $100 USD",
        "sesion_acupuntura": "$50 - $80 USD",
        "consulta_seguimiento": "$40 - $60 USD",
        "medicina_herbal_mensual": "$30 - $70 USD"
    },
    "sintomas_y_causas": {
        "Dolor de cabeza frontal": "Estancamiento de Yangming (estómago/intestino grueso) o ataque de viento-frío",
        "Dolor de cabeza lateral": "Desequilibrio de Hígado / Vesícula Biliar",
        "Dolor de cabeza occipital": "Invasión de viento-frío en el canal Taiyang (vejiga)",
        "Fatiga crónica": "Deficiencia de Qi de Bazo o deficiencia de Yang de Riñón",
        "Insomnio": "Fuego de Corazón o deficiencia de Yin de Riñón",
        "Manos y pies fríos": "Deficiencia de Yang de Bazo o Riñón",
        "Boca seca y sed": "Calor interior o deficiencia de Yin",
        "Palpitaciones": "Deficiencia de sangre del Corazón o flema-calor",
        "Distensión abdominal": "Estancamiento de Qi de Hígado o deficiencia de Bazo",
        "Diarrea": "Deficiencia de Yang de Bazo o humedad-frío"
    },
    "remedios": [
        {"nombre": "Gan Mao Ling", "indicacion": "Resfriado común con calor", "ingredientes": "Isatis, Chrysanthemum, etc."},
        {"nombre": "Xiao Yao San", "indicacion": "Estrés, estancamiento de Hígado", "ingredientes": "Bupleurum, Angelica, Poria"},
        {"nombre": "Liu Wei Di Huang Wan", "indicacion": "Deficiencia de Yin de Riñón", "ingredientes": "Rehmannia, Cornus, Dioscorea"},
        {"nombre": "Gui Pi Tang", "indicacion": "Insomnio, palpitaciones por deficiencia de Bazo/Corazón", "ingredientes": "Ginseng, Jujube, Longan"},
        {"nombre": "Zhen Gu Zai Zao Wan", "indicacion": "Fracturas, dolor óseo", "ingredientes": "Ostrea, Dragon bone, etc."}
    ],
    "caliente_frio": {
        "calor_sintomas": "Fiebre, sed, orina oscura, estreñimiento, irritabilidad",
        "frio_sintomas": "Manos/pies fríos, diarrea, orina clara, falta de energía",
        "alimentos_calientes": "Jengibre, canela, cordero, ajo, pimienta",
        "alimentos_frios": "Pepino, sandía, menta, tofu, berro",
        "consejo": "Equilibrar según patrón: comer más caliente si hay frío, más fresco si hay calor."
    }
}

# ================= FUNCIONES DE RESPUESTA OFFLINE =================
def buscar_en_datos(pregunta):
    """Busca palabras clave en la pregunta y retorna información relevante de TCM_DATA"""
    pregunta_lower = pregunta.lower()
    respuesta = ""

    keywords_map = {
        "dieta": "dietas", "alimento": "dietas", "comer": "dietas", "caliente": "caliente_frio", "frío": "caliente_frio",
        "punto": "puntos_acupuntura", "acupuntura": "puntos_acupuntura", "precio": "precios",
        "síntoma": "sintomas_y_causas", "sintoma": "sintomas_y_causas", "causa": "sintomas_y_causas",
        "remedio": "remedios", "hierba": "remedios", "elemento": "elementos", "wuxing": "elementos"
    }

    secciones = set()
    for kw, sec in keywords_map.items():
        if kw in pregunta_lower:
            secciones.add(sec)

    if not secciones:
        secciones = {"elementos", "dietas", "caliente_frio"}

    for sec in secciones:
        if sec in TCM_DATA:
            respuesta += f"\n\n--- {sec.upper()} ---\n"
            if isinstance(TCM_DATA[sec], list):
                for item in TCM_DATA[sec]:
                    if isinstance(item, dict):
                        respuesta += json.dumps(item, ensure_ascii=False) + "\n"
                    else:
                        respuesta += str(item) + "\n"
            elif isinstance(TCM_DATA[sec], dict):
                for k, v in TCM_DATA[sec].items():
                    respuesta += f"{k}: {v}\n"
            else:
                respuesta += str(TCM_DATA[sec]) + "\n"

    if not respuesta:
        respuesta = "No encontré información exacta en mi base local. Por favor, consulta a un especialista o activa Claude AI."
    return respuesta.strip()

def obtener_respuesta_claude(pregunta):
    """Consulta a Claude API usando la clave de entorno"""
    if not CLAUDE_API_KEY:
        return buscar_en_datos(pregunta) + "\n\n(Modo offline: usa CLAUDE_API_KEY para respuestas más precisas)"
    
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 800,
        "temperature": 0.7,
        "system": "Eres un experto en Medicina Tradicional China (MTC). Hablas español. Tus respuestas deben incluir conceptos de Yin/Yang, cinco elementos, calor/frío, dietas, puntos de acupuntura, remedios, etc. Sé claro y detallado.",
        "messages": [
            {"role": "user", "content": pregunta}
        ]
    }
    try:
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]
    except Exception as e:
        return f"Error al contactar a Claude: {str(e)}. Usando modo offline.\n\n{buscar_en_datos(pregunta)}"

# ================= RUTAS API =================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tcm_data', methods=['GET'])
def get_tcm_data():
    return jsonify(TCM_DATA)

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    pregunta = data.get('question', '')
    if not pregunta:
        return jsonify({"error": "No se recibió pregunta"}), 400
    
    respuesta = obtener_respuesta_claude(pregunta)
    return jsonify({"answer": respuesta})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
