
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(r"c:\Users\Cristian Gonzalez\Desktop\apicollector")

from utils import save_dynamic_photo

def test_save_photo():
    # Mock data
    b64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==" # 1x1 pixel png
    device_id = "TEST-DEVICE"
    fecha = datetime(2026, 4, 1)
    monitoreo_id = 999
    tipo = "general"
    
    print(f"Testing save_dynamic_photo...")
    relative_path = save_dynamic_photo(b64_data, device_id, fecha, monitoreo_id, tipo)
    
    if relative_path:
        print(f"Success! Path: {relative_path}")
        absolute_path = os.path.join("static", relative_path)
        if os.path.exists(absolute_path):
            print(f"File exists at: {absolute_path}")
        else:
            print(f"Error: File NOT found at {absolute_path}")
    else:
        print("Failed to save photo.")

if __name__ == "__main__":
    test_save_photo()
