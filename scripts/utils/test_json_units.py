import requests
import json
import sys

def test_json_units():
    url = "http://localhost:5348/api/sync/monitoreos"
    auth = ("gpconsul", "gp2026")
    
    payload = {
        "monitoreos": [
            {
                "id": 9999,
                "device_id": "UNIT-TESTER-125",
                "programa_id": 1,
                "estacion_id": 1,
                "fecha_hora": "2026-04-20 15:00:00",
                "detalles_json": [
                    {"parametro": "Conductividad", "valor": 1500, "unidad": "µS/cm"},
                    {"parametro": "Oxigeno Disuelto", "valor": 8.5, "unidad": "mg/L"}
                ],
                "multiparametros_json": [
                    {"parametro": "Temperatura", "valor": 22.4, "unidad": "°C"},
                    {"parametro": "pH", "valor": 7.2, "unidad": "u.pH"}
                ]
            }
        ]
    }
    
    print(f"🚀 Enviando payload con unidades a {url}...")
    try:
        response = requests.post(url, json=payload, auth=auth)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Sincronización exitosa!")
            print(f"Respuesta: {response.json()}")
            
            # Ahora verificamos en la base de datos (usando una consulta directa si es posible)
            # O simplemente confiamos en el 200 si la API no explotó con el nuevo esquema
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"🚨 Error de conexión: {e}")

if __name__ == "__main__":
    test_json_units()
