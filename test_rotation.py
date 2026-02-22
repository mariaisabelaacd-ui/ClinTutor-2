from logic import get_groq_client, GROQ_API_KEYS

def test_rotation():
    print(f"Total de chaves carregadas: {len(GROQ_API_KEYS)}")
    print("-" * 40)
    for i in range(10):
        client = get_groq_client()
        if client:
            # Obtém a chave truncada para exibição segura
            safe_key = client.api_key[:10] + "..." + client.api_key[-5:]
            print(f"Requisição {i+1}: Usando a chave -> {safe_key}")
        else:
            print("Erro: Nenhuma chave encontrada.")

if __name__ == "__main__":
    test_rotation()
