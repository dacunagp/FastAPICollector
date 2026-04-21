import requests
import json
import base64

# Simulación de una pequeña imagen Base64 (píxel rojo PNG)
B64_PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

def test_sync_v2_post_fix():
    url = "http://localhost:5348/api/sync/monitoreos"
    auth = ("gpconsul", "gp2026")
    
    payload = {
        "monitoreos": [
            {
                "id": 8686,
                "device_id": "FIX-VERIFY-86",
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora": "2026-04-06 13:00:00",
                "foto_path": B64_PIXEL,
                "detalles": [
                    {"parametro": "Caudal (Fix)", "valor": 7.0},
                    {"parametro": "pH (Fix)", "valor": 8.1}
                ]
            }
        ]
    }
    
    print(f"🚀 Enviando payload de verificación a {url}...")
    try:
        response = requests.post(url, json=payload, auth=auth)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Sincronización exitosa Post-Fix!")
            print(f"Respuesta: {response.json()}")
        else:
            print(f"❌ Error Post-Fix: {response.text}")
            
    except Exception as e:
        print(f"🚨 Error de conexión: {e}")

if __name__ == "__main__":
    test_sync_v2_post_fix()
