from jose import JWTError,jwt
from datetime import datetime,timedelta
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi import HTTPException,status,Depends
from app.schemas import TokenData
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
import app.models
from datetime import datetime, timedelta, timezone
load_dotenv()
# Configuration settings
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM=os.getenv("ALGORITHM", "HS256")
SECRET_KEY=os.getenv("SECRET_KEY")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl='login')
# Function to create access token
def create_access_token(data:dict):
    """
    Create a JWT access token.
    """
    to_encode=data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt
# Function to verify access token
def verify_access_token(token:str,credentials_exception):
    """
    Verify a JWT access token and extract the token data.
    """
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        id:str=payload.get("user_id")
        if id is None:
            raise credentials_exception
        id_=int(id)
        token_data=TokenData(id=id_)
        return token_data
    except JWTError:
        raise credentials_exception
# Dependency to get the current authenticated user
def get_current_user(token:str=Depends(oauth2_scheme),db: Session = Depends(get_db)):
    """
    Retrieve the current authenticated user based on the access token.
    """
    credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})
    token=verify_access_token(token,credentials_exception)
    current_user = db.query(app.models.User).filter(app.models.User.id == token.id).first()
    if current_user is None:
        raise credentials_exception
    return current_user

