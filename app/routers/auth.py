from fastapi import FastAPI, HTTPException, Depends, status, APIRouter,Request
from app.database import get_db
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import app.models
from app.schemas import UserLogin,Token
from app.utils import verify
from app.oauth2 import create_access_token
from slowapi import Limiter  
from slowapi.util import get_remote_address  
router=APIRouter(
    tags=["Authentication"]
)
limiter = Limiter(key_func=get_remote_address)# Rate limiter instance
@router.post("/login",response_model=Token)
@limiter.limit("5/minute")# Rate limit: 5 requests per minute
async def login(request: Request,
          user_credentials:OAuth2PasswordRequestForm=Depends(),
          db:Session=Depends(get_db))->Token:
   """  Authenticate a user and generate an access token.
        Rate Limit: 5 requests per minute
   Args: 
         request: HTTP request object
         user_credentials: User login credentials
         db: Database session
   Returns:
            Access token and token type
   """
   try:
       user=(
        db.query(app.models.User)
        .filter(app.models.User.email==user_credentials.username)
        .first()
        )
       if not user:
               raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
       if not verify(user_credentials.password,user.password):
               raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Credentials")
       access_token=create_access_token(data={"user_id":user.id})
       return {"access_token":access_token,"token_type":"bearer"}
   except HTTPException as e:
        raise e
   except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
   except Exception as e:
        
        raise HTTPException(status_code=500, detail=str(e))