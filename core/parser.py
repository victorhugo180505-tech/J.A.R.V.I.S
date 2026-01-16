import json

def parse_response(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("La IA no devolvió JSON válido")
