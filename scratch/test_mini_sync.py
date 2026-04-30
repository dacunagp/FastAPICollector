import httpx
import json

API_USER = "collector"
API_PASS = "gp2026"
BASE_URL = "http://localhost:5348/api"

def test_sync_no_signature():
    url = f"{BASE_URL}/sync/monitoreos"
    payload = {
        "monitoreos": [
            {
                "device_id": "TEST_DEVICE_MINI",
                "id_local": 8888,
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora": "2026-04-23 12:00:00",
                "monitoreo_fallido": 0,
                "observacion": "Test sync without signature"
            }
        ]
    }
    
    data = {
        "payload": json.dumps(payload)
    }
    
    print("Sending request...")
    try:
        response = httpx.post(
            url, 
            data=data, 
            auth=(API_USER, API_PASS),
            timeout=10.0
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sync_no_signature()
