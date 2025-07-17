import asyncio
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.models import User, UserRole
from core.security import get_password_hash
import sys

def create_admin_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"Usuário com email {email} já existe. Alterando para ADMIN.")
        user.role = UserRole.ADMIN
    else:
        print(f"Criando novo usuário ADMIN com email {email}.")
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            first_name="Admin",
            last_name="System"
        )
        db.add(user)
    
    db.commit()
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python create_admin.py <email> <senha>")
        sys.exit(1)
        
    admin_email = sys.argv[1]
    admin_password = sys.argv[2]
    
    db = SessionLocal()
    try:
        create_admin_user(db, admin_email, admin_password)
    finally:
        db.close()