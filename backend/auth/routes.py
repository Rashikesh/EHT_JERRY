from fastapi import APIRouter, Depends, HTTPException, status, Response , Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db
from database.models import User, ActivityLog
from auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from auth.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth", tags=["authentication"])

limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Rate limit registration
async def register(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log activity
    activity = ActivityLog(
        user_id=db_user.id,
        action="account_created",
        metadata={"ip": request.client.host}
    )
    db.add(activity)
    db.commit()
    
    return db_user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Rate limit login to prevent brute force
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get JWT tokens"""
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Log activity
    activity = ActivityLog(
        user_id=user.id,
        action="login",
        metadata={"ip": request.client.host}
    )
    db.add(activity)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    payload = verify_token(token_data.refresh_token, "refresh")
    username: str = payload.get("sub")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout and log activity"""
    activity = ActivityLog(
        user_id=current_user.id,
        action="logout",
        metadata={"ip": request.client.host}
    )
    db.add(activity)
    db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user