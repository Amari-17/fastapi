import time
from typing import List
from fastapi import Depends, FastAPI, Response, status, HTTPException
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row
from . import models, schemas, utils
from sqlalchemy.orm import Session
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


class Post(BaseModel):
    title: str
    content: str
    published: bool = True


while True:
    try:
        conn = psycopg.connect(host="localhost",
                               dbname="fastapi",
                               user="postgres",
                               password="admin",
                               row_factory=dict_row)
        cur = conn.cursor()
        print("Database connection was successfull!.")
        break
    except Exception as error:
        print("Connection was Failed!!")
        print(f"Error: {error}")
        time.sleep(5)


my_posts = [{"title": "SuperShy a hit song", "content": "New Jeans new song"
             " Super Shy was a absolute hit.", "id": 1},
            {"title": "Queen of Korean Beauti", "content": "Blackpink Jisoo"
             " away will be the Queen of Korean Faces.", "id": 2}]


def find_post(id):
    for post in my_posts:
        if id == post["id"]:
            return post


def find_post_index(id):
    for i, p in enumerate(my_posts):
        if p["id"] == id:
            return i


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/posts")
async def get_posts(db: Session = Depends(get_db)):
    # cur.execute("""SELECT * FROM posts""")
    # posts = cur.fetchall()
    posts = db.query(models.Post).all()
    return {"data": posts}


@app.get("/posts/{id}")
async def get_post(id: int, db: Session = Depends(get_db)):
    # cur.execute("""SELECT * FROM posts WHERE id = (%s) """, (str(id),))
    # post = cur.fetchone()
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found")
    return {"details": post}


@app.post("/posts",  status_code=status.HTTP_201_CREATED)
async def create_post(post: Post, db: Session = Depends(get_db)):
    # cur.execute("""INSERT into posts (title, content, published)
    #             VALUES (%s, %s, %s) RETURNING * """,
    #             (post.title, post.content, post.published))
    # new_post = cur.fetchone()
    # conn.commit()
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"data": new_post}


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int, db: Session = Depends(get_db)):
    # cur.execute("""DELETE FROM posts WHERE
    #                             id = (%s) RETURNING * """, (str(id),))
    # deleted_post = cur.fetchone()
    # conn.commit()
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found.")
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}", status_code=status.HTTP_202_ACCEPTED)
async def update_post(id: int, post: Post, db: Session = Depends(get_db)):
    # cur.execute("""UPDATE posts SET title=%s ,content=%s,
    #              published=%s WHERE id = %s RETURNING * """,
    #             (post.title, post.content, post.published, str(id)))
    # updated_post = cur.fetchone()
    # conn.commit()
    post_query = db.query(models.Post).filter(models.Post.id == id)
    db_post = post_query.first()
    if db_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found.")
    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    db_post = post_query.first()
    return {"data": db_post}


@app.get("/posts", response_model=List[schemas.Post])
async def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return posts


@app.get("/posts/{id}", response_model=schemas.Post)
async def get_post(id: int,
                   db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found")
    return post


@app.post("/posts",  status_code=status.HTTP_201_CREATED,
          response_model=schemas.Post)
async def create_post(post: schemas.PostCreate,
                      db: Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int,
                      db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found.")
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}", status_code=status.HTTP_202_ACCEPTED,
         response_model=schemas.Post)
async def update_post(id: int, post: schemas.PostCreate,
                      db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    db_post = post_query.first()
    if db_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID:{id} was not found.")
    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    db_post = post_query.first()
    return db_post


@app.get("/users/{id}", response_model=schemas.UserOut)
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with ID: {id} was not found.")
    return user


@app.post("/users", status_code=status.HTTP_201_CREATED,
          response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate,
                      db: Session = Depends(get_db)):
    user.password = utils.hash(user.password)

    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
