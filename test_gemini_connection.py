
import google.generativeai as genai
import streamlit as st
import os

# Tenta pegar a chave do arquivo de secrets local para teste
try:
    import toml
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["google_api"]["api_key"]
    print(f"Chave encontrada: {api_key[:5]}...")
except Exception as e:
    print(f"Erro ao ler secrets: {e}")
    # Fallback para a chave fornecida pelo usuário no chat para teste direto
    api_key = "AIzaSyADRXQY65M1NdyJdocfvFzRuzNgWZNoPbg"

genai.configure(api_key=api_key)

print("Tentando listar modelos disponíveis...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Erro ao listar modelos: {e}")

print("\nTentando gerar conteúdo com 'gemini-2.0-flash'...")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Oi, isso é um teste.")
    print(f"Sucesso (2.0-flash): {response.text}")
except Exception as e:
    print(f"Erro com gemini-2.0-flash: {e}")

print("\nTentando gerar conteúdo com 'gemini-1.5-flash' (alternativa)...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Oi, isso é um teste.")
    print(f"Sucesso (1.5-flash): {response.text}")
except Exception as e:
    print(f"Erro com gemini-1.5-flash: {e}")
