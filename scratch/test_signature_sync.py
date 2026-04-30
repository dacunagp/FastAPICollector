import httpx
import json
import os

# Credenciales (Basic Auth)
API_USER = "collector"
API_PASS = "gp2026"
BASE_URL = "http://localhost:5348/api"

def test_sync_with_signature():
    url = f"{BASE_URL}/sync/monitoreos"
    
    # Payload JSON
    payload = {
        "monitoreos": [
            {
                "device_id": "TEST_DEVICE_001",
                "id_local": 9999,
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora": "2026-04-23 12:00:00",
                "monitoreo_fallido": 0,
                "observacion": "Test sync with signature"
            }
        ]
    }
    
    # Archivo de firma
    with open("scratch/mock_signature.jpg", "rb") as f:
        files = {
            "firma_operador": ("firma.jpg", f, "image/jpeg")
        }
        data = {
            "payload": json.dumps(payload)
        }
        
        response = httpx.post(
            url, 
            data=data, 
            files=files, 
            auth=(API_USER, API_PASS),
            timeout=30.0
        )
        
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_sync_with_signature()
