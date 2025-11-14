from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, Request
from app.database import get_db
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import app.models
from app.schemas import UserLogin, Token
from app.utils import verify, hash  
from app.oauth2 import create_access_token
from slowapi import Limiter  
from slowapi.util import get_remote_address  
import logging
import traceback

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

router = APIRouter(tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """Authenticate a user and generate an access token."""
    
    try:
        logger.info(f"Login attempt for email: {user_credentials.username}")
        
        # Step 1: Find user
        user = db.query(app.models.User).filter(
            app.models.User.email == user_credentials.username
        ).first()
        
        if not user:
            logger.warning(f"User not found: {user_credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User found: {user.email}")
        logger.debug(f" Password in DB: {user.password[:20]}...")  # First 20 chars
        logger.debug(f" Password type: {type(user.password)}")
        
        # Step 2: Verify password
        logger.info("Verifying password...")
        
        is_password_valid = verify(user_credentials.password, user.password)
        
        logger.info(f" Password verification result: {is_password_valid}")
        
        if not is_password_valid:
            logger.warning(f" Invalid password for: {user_credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Credentials"
            )
        
        # Step 3: Create token
        logger.info(f" Creating access token for user {user.id}")
        access_token = create_access_token(data={"user_id": user.id})
        
        logger.info(f" Login successful for: {user_credentials.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
    
    except Exception as e:
        logger.error(f" Unexpected error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(traceback.format_exc())  
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")