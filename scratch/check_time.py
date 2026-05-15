from datetime import datetime
import os
import time

print(f"Local time: {datetime.now()}")
print(f"UTC time: {datetime.utcnow()}")
try:
    from zoneinfo import ZoneInfo
    print(f"Chile time: {datetime.now(ZoneInfo('America/Santiago'))}")
except Exception as e:
    print(f"ZoneInfo error: {e}")
