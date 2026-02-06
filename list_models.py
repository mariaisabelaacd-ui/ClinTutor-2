
import google.generativeai as genai
import os

api_key = "AIzaSyADRXQY65M1NdyJdocfvFzRuzNgWZNoPbg"
genai.configure(api_key=api_key)

print("--- LISTANDO MODELOS DISPONÍVEIS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Nome: {m.name}")
except Exception as e:
    print(f"ERRO AO LISTAR: {e}")

print("\n--- TESTANDO gemini-1.5-flash-latest ---")
try:
    # Tentando variation 'latest' que as vezes resolve cache
    model = genai.GenerativeModel('gemini-1.5-flash-latest') 
    print("Sucesso: ", model.generate_content("Oi").text)
except Exception as e:
    print(f"Erro: {e}")
