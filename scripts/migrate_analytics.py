import sys
import os
import json
import time

# Permite importar arquivos do app principal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from analytics import get_all_users_analytics_firebase, get_all_dbs, is_firebase_connected
from logic import QUESTIONS, evaluate_answer_with_ai

q_map = {q['id']: q for q in QUESTIONS}

def run_migration():
    print("Iniciando migracao do banco de dados (avaliando questoes legadas)...")
    if not is_firebase_connected():
        print("Erro: Firebase nao esta conectado.")
        return
        
    all_dbs = get_all_dbs()
    if not all_dbs:
        print("Erro: Nenhum banco de dados retornado.")
        return
        
    for db in all_dbs:
        # Busca casos
        case_docs = db.collection('case_analytics').get()
        print(f"Lendo base de dados {db.project} - {len(case_docs)} registros encontrados.")
        
        atualizados = 0
        pulados = 0
        erros = 0
        
        for doc in case_docs:
            data = doc.to_dict()
            result = data.get("case_result", {})
            
            # Re-avalia TODOS os registros com o prompt atualizado (mais rigoroso)
            # Se já tem criterios, força reavaliação para aplicar o novo prompt
                
            cid = data.get("case_id")
            q_data = q_map.get(cid)
            
            if not q_data:
                pulados += 1
                continue
                
            user_answer = result.get("user_answer", "Ausente ou não registrada")
            
            # Pede à IA para reconstruir os criterios para o texto antigo
            print(f"Re-avaliando resposta do usuario {data.get('user_id')}...")
            ai_evaluation = evaluate_answer_with_ai(q_data, user_answer)
            
            if "criterios" in ai_evaluation:
                result["criterios"] = ai_evaluation["criterios"]
                # Atualizando os pontos
                points = 0.0
                for crit, status in result["criterios"].items():
                    if "Completa" in status:
                        points += 1.0
                    elif "Parcial" in status:
                        points += 0.5
                if points > 5.0: points = 5.0
                
                result["points_gained"] = float(points)
                result["feedback"] = ai_evaluation.get("feedback", result.get("feedback", ""))
                
                # Atualiza no firebase
                try:
                    db.collection('case_analytics').document(doc.id).update({
                        "case_result": result
                    })
                    atualizados += 1
                except Exception as e:
                    print(f"Erro ao atualizar doc {doc.id}: {e}")
                    erros += 1
            else:
                print(f"Falha na IA para a resposta {doc.id}: {ai_evaluation}")
                erros += 1
                
        print(f"\nFinalizado BD. \nAtualizados: {atualizados} | Pulados: {pulados} | Erros de IA: {erros}\n")

if __name__ == "__main__":
    run_migration()
