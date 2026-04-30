import requests
import json
import base64
import os

API_USER = "collector"
API_PASS = "gp2026"
BASE_URL = "http://localhost:5348/api"

def test_photo_sync_mixed():
    """ 
    Prueba sincronización con:
    1. Un registro con foto Base64 en el JSON.
    2. Un registro con foto vía Multipart.
    3. Una firma vía Multipart para ambos (Batch-wide).
    """
    url = f"{BASE_URL}/sync/monitoreos"
    
    # Dummy image data (red pixel)
    dummy_img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    dummy_bytes = base64.b64decode(dummy_img_b64)

    payload = {
        "monitoreos": [
            {
                "device_id": "TEST_SYNC_PHOTOS",
                "id_local": 1001,
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora": "2026-04-23 15:00:00",
                "observacion": "Registro con foto Base64",
                "foto_path": dummy_img_b64 # Base64 en el JSON
            },
            {
                "device_id": "TEST_SYNC_PHOTOS",
                "id_local": 1002,
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora": "2026-04-23 15:05:00",
                "observacion": "Registro que usará foto multipart"
            }
        ]
    }
    
    data = {
        "payload": json.dumps(payload)
    }
    
    # Archivos Multipart
    files = {
        "foto_path": ("general.jpg", dummy_bytes, "image/jpeg"),
        "firma_operador": ("firma.jpg", dummy_bytes, "image/jpeg")
    }
    
    print("🚀 Enviando sincronización con fotos...")
    try:
        response = requests.post(
            url, 
            data=data,
            files=files,
            auth=(API_USER, API_PASS),
            timeout=15.0
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Sincronización exitosa.")
        else:
            print("❌ Error en la sincronización.")
            
    except Exception as e:
        print(f"🚨 Error de conexión: {e}")

if __name__ == "__main__":
    test_photo_sync_mixed()
