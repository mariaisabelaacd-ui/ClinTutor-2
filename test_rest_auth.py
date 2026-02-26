import requests
import streamlit as st
import json
from pathlib import Path

def test_rest():
    try:
        import toml
        secrets_path = Path(".streamlit/secrets.toml")
        secrets_dict = toml.load(secrets_path)
        api_key = secrets_dict.get("google_api", {}).get("api_key")
        
        email = "test@example.com"
        password = "testpassword123"
        
        # We don't have a real test account to login, let's just make the request and see the error message.
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        data = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        res = requests.post(url, json=data)
        print("Status code:", res.status_code)
        print("Response:", res.json())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_rest()
