import json
import requests
from datetime import datetime

# Simular payload
payload = {
    "monitoreos": [
        {
            "id_local": 999,
            "device_id": "TEST-DEVICE",
            "fecha_hora_muestreo": "2026-05-11 20:10:00",
            "fecha_hora": "2026-05-11 20:00:00",
            "programa_id": 1,
            "estacion_id": 1,
            "usuario_id": 1
        }
    ]
}

# Enviar a la API local (asumiendo que corre en el puerto 8000 o similar, pero no puedo)
# En lugar de eso, voy a probar el schema localmente

from schemas import SyncPayload
try:
    obj = SyncPayload(**payload)
    print(f"Parsed fecha_hora_muestreo: {obj.monitoreos[0].fecha_hora_muestreo}")
except Exception as e:
    print(f"Error parsing: {e}")
