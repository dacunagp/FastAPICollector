import requests
import json

def test_optional_id():
    url = "http://localhost:5348/api/sync/monitoreos"
    auth = ("gpconsul", "gp2026")
    
    # Payload WITHOUT 'id' field
    payload = {
        "monitoreos": [
            {
                "device_id": "TEST-OPTIONAL-ID",
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora_muestreo": "2026-04-21 15:00:00",
                "observacion": "Test de ID opcional - Fase 131"
            }
        ]
    }
    
    print(f"🚀 Enviando payload SIN ID a {url}...")
    try:
        response = requests.post(url, json=payload, auth=auth)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Sincronización exitosa SIN ID!")
            print(f"Respuesta: {response.json()}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Cuerpo: {response.text}")
            
    except Exception as e:
        print(f"🚨 Error de conexión: {e}")

if __name__ == "__main__":
    test_optional_id()
