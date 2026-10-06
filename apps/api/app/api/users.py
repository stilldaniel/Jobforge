from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    NotificationPreferences,
    NotificationPreferencesUpdate,
    UserCreate,
    UserResponse,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        timezone=user_data.timezone,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user

def get_user_or_404(
    db: Session,
    user_id: int,
) -> User:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.get(
    "/{user_id}/notification-preferences",
    response_model=NotificationPreferences,
)
def get_notification_preferences(
    user_id: int,
    db: Session = Depends(get_db),
):
    return get_user_or_404(db, user_id)


@router.patch(
    "/{user_id}/notification-preferences",
    response_model=NotificationPreferences,
)
def update_notification_preferences(
    user_id: int,
    preferences: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
):
    user = get_user_or_404(db, user_id)

    for field, value in preferences.model_dump(
        exclude_none=True,
    ).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    user.email = user_data.email
    user.full_name = user_data.full_name
    user.timezone = user_data.timezone

    db.commit()
    db.refresh(user)

    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully",
        "user_id": user_id,
    }