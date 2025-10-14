#!/usr/bin/env python3
"""
Script para testar o sistema de analytics
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analytics import (
    start_case_timer, end_case_timer, log_chat_interaction,
    get_user_detailed_stats, get_all_users_analytics, get_global_stats,
    format_duration
)
from auth_firebase import get_all_users

def test_analytics_system():
    """Testa o sistema de analytics"""
    print("Testando Sistema de Analytics...")
    print("=" * 50)
    
    # Busca usuários
    users = get_all_users()
    students = [user for user in users if user.get('user_type') == 'aluno']
    
    if not students:
        print("ERRO: Nenhum aluno encontrado para testar.")
        return False
    
    test_student = students[0]
    print(f"Testando com aluno: {test_student['name']}")
    print()
    
    # Teste 1: Estatísticas do usuário
    print("1. Testando estatísticas do usuário...")
    try:
        user_stats = get_user_detailed_stats(test_student['id'])
        print(f"   Casos resolvidos: {user_stats['case_stats']['total_cases']}")
        print(f"   Taxa de acertos: {user_stats['case_stats']['accuracy_rate']:.1f}%")
        print(f"   Tempo médio: {user_stats['case_stats']['average_time_formatted']}")
        print(f"   Interações chat: {user_stats['total_chat_interactions']}")
        print("   SUCESSO: Estatísticas carregadas!")
    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Teste 2: Analytics globais
    print("2. Testando analytics globais...")
    try:
        global_stats = get_global_stats()
        print(f"   Total de usuários: {global_stats.get('total_users', 0)}")
        print(f"   Total de casos: {global_stats.get('total_cases', 0)}")
        print(f"   Total de interações chat: {global_stats.get('total_chat_interactions', 0)}")
        print(f"   Taxa média de acertos: {global_stats.get('average_accuracy_rate', 0):.1f}%")
        print("   SUCESSO: Analytics globais carregados!")
    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Teste 3: Simulação de timer de caso
    print("3. Testando timer de caso...")
    try:
        timer_id = start_case_timer(test_student['id'], "test_case_123")
        print(f"   Timer iniciado: {timer_id}")
        
        # Simula resultado do caso
        case_result = {
            "points_gained": 15,
            "breakdown": {
                "diagnóstico": 10,
                "exames": 3,
                "plano": 2,
                "bônus_streak": 0
            }
        }
        
        analytics_data = end_case_timer(timer_id, case_result)
        if analytics_data:
            print(f"   Timer finalizado: {analytics_data['duration_formatted']}")
            print("   SUCESSO: Timer funcionando!")
        else:
            print("   ERRO: Falha ao finalizar timer")
            return False
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    print()
    
    # Teste 4: Simulação de interação com chat
    print("4. Testando interação com chat...")
    try:
        log_chat_interaction(
            test_student['id'],
            "test_case_123",
            "Qual é o diagnóstico mais provável?",
            "Vamos analisar os sintomas juntos. Que achados você observou?",
            2.5
        )
        print("   SUCESSO: Interação do chat registrada!")
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    print()
    
    # Teste 5: Analytics de todos os usuários
    print("5. Testando analytics de todos os usuários...")
    try:
        all_analytics = get_all_users_analytics()
        print(f"   Usuários com analytics: {len(all_analytics)}")
        
        for user_id, data in all_analytics.items():
            case_count = len(data.get('case_analytics', []))
            chat_count = len(data.get('chat_interactions', []))
            print(f"   - Usuário {user_id}: {case_count} casos, {chat_count} interações chat")
        
        print("   SUCESSO: Analytics de todos os usuários carregados!")
    except Exception as e:
        print(f"   ERRO: {e}")
        return False
    
    print()
    print("=" * 50)
    print("SUCESSO: Todos os testes passaram!")
    return True

def show_analytics_summary():
    """Mostra resumo dos analytics"""
    print("Resumo dos Analytics...")
    print("=" * 50)
    
    try:
        global_stats = get_global_stats()
        print(f"Total de usuários: {global_stats.get('total_users', 0)}")
        print(f"Total de casos: {global_stats.get('total_cases', 0)}")
        print(f"Total de interações chat: {global_stats.get('total_chat_interactions', 0)}")
        print(f"Taxa média de acertos: {global_stats.get('average_accuracy_rate', 0):.1f}%")
        print(f"Usuários ativos hoje: {global_stats.get('active_users_today', 0)}")
        
        print()
        print("Detalhes por usuário:")
        
        users = get_all_users()
        for user in users:
            if user.get('user_type') == 'aluno':
                user_stats = get_user_detailed_stats(user['id'])
                print(f"- {user['name']}: {user_stats['case_stats']['total_cases']} casos, {user_stats['case_stats']['accuracy_rate']:.1f}% acertos")
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    print("ClinTutor - Teste do Sistema de Analytics")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        show_analytics_summary()
    else:
        test_analytics_system()
