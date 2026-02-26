import sys
import os

# Ensure the app imports work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_firebase import register_user, authenticate_user, delete_user
import uuid

def test_login_flow():
    # Make a unique email to avoid conflicts if it persists
    test_email = f"test_{uuid.uuid4().hex[:6]}@aluno.fcmsantacasasp.edu.br"
    test_password = "password123"
    
    print(f"Testing with {test_email}...")
    
    # Register user
    success, msg = register_user(
        name="Aluno Teste",
        email=test_email,
        password=test_password,
        user_type="aluno",
        ra="123456"
    )
    print("Registration:", success, msg)
    if not success:
        return

    # Attempt login with WRONG password
    success, msg, data = authenticate_user(test_email, "wrongpassword")
    print("Login (wrong password):", success, msg)
    assert not success, "Should fail with wrong password!"
    
    # Attempt login with RIGHT password
    success, msg, data = authenticate_user(test_email, test_password)
    print("Login (right password):", success, msg)
    assert success, "Should succeed with right password!"
    
    if data:
        # Clean up
        uid = data.get('id')
        del_success, del_msg = delete_user(uid)
        print("Cleanup:", del_success, del_msg)

if __name__ == "__main__":
    test_login_flow()
