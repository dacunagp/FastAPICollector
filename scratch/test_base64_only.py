import requests
import json
import base64
import os

API_USER = "collector"
API_PASS = "gp2026"
BASE_URL = "http://localhost:5348/api"

def test_base64_only():
    url = f"{BASE_URL}/sync/monitoreos"
    
    # Dummy image data (blue pixel)
    dummy_img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPj/HwADBwF7+A9A6wAAAABJRU5ErkJggg=="

    payload = {
        "monitoreos": [
            {
                "device_id": "TEST_BASE64_ONLY",
                "id_local": 2001,
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora_muestreo": "2026-04-23 15:15:00",
                "observacion": "Registro con solo foto Base64",
                "foto_path": dummy_img_b64,
                "firma_path": dummy_img_b64
            }
        ]
    }
    
    data = { "payload": json.dumps(payload) }
    
    print("🚀 Enviando sincronización Base64 ONLY...")
    try:
        response = requests.post(url, data=data, auth=(API_USER, API_PASS), timeout=15.0)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"🚨 Error: {e}")

if __name__ == "__main__":
    test_base64_only()
