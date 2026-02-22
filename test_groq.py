import sys
import os

from logic import evaluate_answer_with_ai, tutor_reply_com_ia, QUESTIONS

def test_groq():
    print("Testing Evaluate Answer...")
    q = QUESTIONS[0]
    ans = "Uma base, um açúcar pentose e grupos fosfato."
    res = evaluate_answer_with_ai(q, ans)
    print("Evaluate Answer Result:")
    print(res)

    print("\nTesting Tutor Reply Stream...")
    chat = []
    gen = tutor_reply_com_ia(q, "Não lembro direito, o que tem nele além de açúcar?", chat)
    print("Tutor Reply Result:")
    for chunk in gen:
        print(chunk, end="", flush=True)
    print("\n\nDone.")

if __name__ == "__main__":
    test_groq()
