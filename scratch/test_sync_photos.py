import requests
import json
import os

# Configuration
URL = "http://localhost:5348/api/sync/monitoreos" # Using port 5348 as per conversation history
AUTH = ("gpconsul", "gp2026")

# Sample Payload
payload_data = {
    "monitoreos": [
        {
            "id_local": 9999,
            "device_id": "TEST_DEVICE",
            "programa_id": 1,
            "estacion_id": 1,
            "fecha_hora_muestreo": "2026-04-23 14:40:00",
            "monitoreo_fallido": 0,
            "observacion": "Test with multipart photos",
            "is_draft": 0
        }
    ]
}

# Create dummy files
with open("scratch/dummy_path.jpg", "wb") as f:
    f.write(b"dummy content path")
with open("scratch/dummy_multi.jpg", "wb") as f:
    f.write(b"dummy content multi")
with open("scratch/dummy_nivel.jpg", "wb") as f:
    f.write(b"dummy content nivel")

files = {
    "payload": (None, json.dumps(payload_data), "application/json"),
    "foto_path": ("foto_path.jpg", open("scratch/dummy_path.jpg", "rb"), "image/jpeg"),
    "foto_multiparametro": ("foto_multiparametro.jpg", open("scratch/dummy_multi.jpg", "rb"), "image/jpeg"),
    "foto_nivel_freatico": ("foto_nivel_freatico.jpg", open("scratch/dummy_nivel.jpg", "rb"), "image/jpeg"),
}

print(f"Sending request to {URL}...")
try:
    response = requests.post(URL, files=files, auth=AUTH)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Close files
    for key in files:
        if isinstance(files[key], tuple) and hasattr(files[key][1], "close"):
            files[key][1].close()
