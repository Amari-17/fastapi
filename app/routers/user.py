from fastapi import Depends, APIRouter, status, HTTPException
from .. import models, schemas, utils
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.get("/{id}", response_model=schemas.UserOut)
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with ID: {id} was not found.")
    return user


@router.post("/", status_code=status.HTTP_201_CREATED,
             response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate,
                      db: Session = Depends(get_db)):
    user.password = utils.hash(user.password)

    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
