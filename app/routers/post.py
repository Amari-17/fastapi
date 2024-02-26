from fastapi import Depends, APIRouter, Response, status, HTTPException
from .. import models, schemas, oauth2
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from typing import List, Optional

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)


@router.get("/", response_model=List[schemas.PostOut])
async def get_posts(db: Session = Depends(get_db),
                    limit: int = 10,
                    skip: int = 0,
                    search: Optional[str] = ""):
    post = db.query(models.Post, func.count(models.Vote.post_id).label("vote")
                    ).join(models.Vote,
                           models.Post.id == models.Vote.post_id,
                           isouter=True).group_by(models.Post.id)
    posts = post.filter(models.Post.title.contains(search))
    posts = posts.limit(limit).offset(skip).all()

    return post


@router.get("/{id}", response_model=schemas.PostOut)
async def get_post(id: int,
                   db: Session = Depends(get_db),
                   current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models.Post, func.count(models.Vote.post_id).label("vote")
                    ).join(models.Vote,
                           models.Post.id == models.Vote.post_id,
                           isouter=True).group_by(models.Post.id)
    post = post.filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found")
    return post


@router.post("/",  status_code=status.HTTP_201_CREATED,
             response_model=schemas.Post)
async def create_post(post: schemas.PostCreate,
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):
    new_post = models.Post(owner_id=current_user.id, **post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int,
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found.")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Post Owners can delete their posts.")
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED,
            response_model=schemas.Post)
async def update_post(id: int, post: schemas.PostCreate,
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    db_post = post_query.first()
    if db_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found.")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Post Owners can delete their posts.")
    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    db_post = post_query.first()
    return db_post
