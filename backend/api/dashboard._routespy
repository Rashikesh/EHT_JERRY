from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database.database import get_db
from database.models import User, Site, Point, ActivityLog, ErrorLog
from auth.security import get_current_active_user, require_role
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Response schemas
class DashboardSummary(BaseModel):
    total_sites: int
    open_points: int
    closed_points: int
    recent_errors: int
    active_users: int

class ActivityResponse(BaseModel):
    id: int
    user_id: int
    site_id: Optional[int]
    action: str
    timestamp: datetime
    metadata: Optional[dict]
    username: str
    
    class Config:
        from_attributes = True

class PointResponse(BaseModel):
    id: int
    site_id: int
    title: str
    status: str
    severity: str
    description: Optional[str]
    created_at: datetime
    closed_at: Optional[datetime]
    closed_by: Optional[int]
    site_name: str
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    id: int
    site_id: int
    error_type: str
    message: str
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime]
    site_name: str
    
    class Config:
        from_attributes = True

class SiteResponse(BaseModel):
    id: int
    name: str
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    created_at: datetime
    owner_id: int
    
    class Config:
        from_attributes = True

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary statistics"""
    # Get user's sites
    user_sites = db.query(Site).filter(Site.owner_id == current_user.id).all()
    site_ids = [site.id for site in user_sites]
    
    if not site_ids:
        return DashboardSummary(
            total_sites=0,
            open_points=0,
            closed_points=0,
            recent_errors=0,
            active_users=1
        )
    
    # Count points
    open_points = db.query(Point).filter(
        Point.site_id.in_(site_ids),
        Point.status == "open"
    ).count()
    
    closed_points = db.query(Point).filter(
        Point.site_id.in_(site_ids),
        Point.status == "closed"
    ).count()
    
    # Count recent errors (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_errors = db.query(ErrorLog).filter(
        ErrorLog.site_id.in_(site_ids),
        ErrorLog.timestamp >= seven_days_ago
    ).count()
    
    return DashboardSummary(
        total_sites=len(user_sites),
        open_points=open_points,
        closed_points=closed_points,
        recent_errors=recent_errors,
        active_users=1
    )

@router.get("/activity", response_model=List[ActivityResponse])
async def get_activity_log(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated activity log"""
    activities = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id
    ).order_by(
        ActivityLog.timestamp.desc()
    ).offset(offset).limit(limit).all()
    
    # Add username to response
    result = []
    for activity in activities:
        activity_dict = {
            "id": activity.id,
            "user_id": activity.user_id,
            "site_id": activity.site_id,
            "action": activity.action,
            "timestamp": activity.timestamp,
            "metadata": activity.metadata,
            "username": current_user.username
        }
        result.append(activity_dict)
    
    return result

@router.get("/points", response_model=List[PointResponse])
async def get_points(
    status: Optional[str] = Query(default=None, pattern="^(open|closed)$"),
    severity: Optional[str] = Query(default=None, pattern="^(low|medium|high|critical)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get points with optional filters"""
    # Get user's sites
    user_sites = db.query(Site).filter(Site.owner_id == current_user.id).all()
    site_ids = [site.id for site in user_sites]
    
    if not site_ids:
        return []
    
    # Build query
    query = db.query(Point).filter(Point.site_id.in_(site_ids))
    
    if status:
        query = query.filter(Point.status == status)
    
    if severity:
        query = query.filter(Point.severity == severity)
    
    points = query.order_by(Point.created_at.desc()).offset(offset).limit(limit).all()
    
    # Add site name to response
    result = []
    for point in points:
        site = db.query(Site).filter(Site.id == point.site_id).first()
        point_dict = {
            "id": point.id,
            "site_id": point.site_id,
            "title": point.title,
            "status": point.status,
            "severity": point.severity,
            "description": point.description,
            "created_at": point.created_at,
            "closed_at": point.closed_at,
            "closed_by": point.closed_by,
            "site_name": site.name if site else "Unknown"
        }
        result.append(point_dict)
    
    return result

@router.get("/errors", response_model=List[ErrorResponse])
async def get_error_history(
    resolved: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get error history with optional filters"""
    # Get user's sites
    user_sites = db.query(Site).filter(Site.owner_id == current_user.id).all()
    site_ids = [site.id for site in user_sites]
    
    if not site_ids:
        return []
    
    # Build query
    query = db.query(ErrorLog).filter(ErrorLog.site_id.in_(site_ids))
    
    if resolved is not None:
        query = query.filter(ErrorLog.resolved == resolved)
    
    errors = query.order_by(ErrorLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    # Add site name to response
    result = []
    for error in errors:
        site = db.query(Site).filter(Site.id == error.site_id).first()
        error_dict = {
            "id": error.id,
            "site_id": error.site_id,
            "error_type": error.error_type,
            "message": error.message,
            "timestamp": error.timestamp,
            "resolved": error.resolved,
            "resolved_at": error.resolved_at,
            "site_name": site.name if site else "Unknown"
        }
        result.append(error_dict)
    
    return result

@router.get("/sites", response_model=List[SiteResponse])
async def get_sites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all sites owned by current user"""
    sites = db.query(Site).filter(Site.owner_id == current_user.id).all()
    return sites