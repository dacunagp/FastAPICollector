import os
from dotenv import load_dotenv
import secrets

# Mock HTTPBasicCredentials
class MockCredentials:
    def __init__(self, username, password):
        self.username = username
        self.password = password

def test_auth():
    load_dotenv()
    api_usernames = os.getenv("API_USERNAMES", "").split(",")
    api_password = os.getenv("API_PASSWORD", "")
    
    print(f"Usernames from .env: {api_usernames}")
    print(f"Password from .env: {api_password}")
    
    # Test valid
    test_user = "gpconsul"
    test_pass = "gp2026"
    
    is_user_valid = test_user in api_usernames
    is_pass_valid = secrets.compare_digest(test_pass, api_password)
    
    print(f"Testing {test_user}/{test_pass}: User Valid={is_user_valid}, Pass Valid={is_pass_valid}")
    
    assert is_user_valid == True
    assert is_pass_valid == True
    print("✅ Logic verification successful!")

if __name__ == "__main__":
    test_auth()
