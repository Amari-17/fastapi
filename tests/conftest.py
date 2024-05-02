from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db, Base
from app.main import app
from app.config import settings
from app.oauth2 import create_token
from app import models
import pytest


SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:"\
    f"{settings.database_password}@{settings.database_hostname}/"\
    f"{settings.database_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def test_user(test_client):
    user_data = {'email': 'tests@example.com',
                 'password': '123456'}
    response = test_client.post("/users/", json=user_data)
    assert response.status_code == 201
    new_user = response.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture
def test_user_2(test_client):
    user_data = {'email': 'test@example.com',
                 'password': '123456'}
    response = test_client.post("/users/", json=user_data)
    assert response.status_code == 201
    new_user = response.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture
def token(test_user):
    return create_token({'user_id': test_user['id']})


@pytest.fixture
def authorized_client(test_client, token):
    test_client.headers = {
        **test_client.headers,
        'Authorization': f'Bearer {token}'
    }
    return test_client


@pytest.fixture
def test_posts(test_user, session, test_user_2):
    posts = [{
        'title': 'first title',
        'content': 'first content',
        'owner_id': test_user['id']
    }, {
        'title': 'second title',
        'content': 'second content',
        'owner_id': test_user['id']
    }, {
        'title': 'third title',
        'content': 'third content',
        'owner_id': test_user['id']
    }, {
        'title': 'fourth title',
        'content': 'fourth content',
        'owner_id': test_user_2['id']
    }]

    def create_post_model(post):
        return models.Post(**post)
    post_map = map(create_post_model, posts)
    posts = list(post_map)

    session.add_all(posts)
    session.commit()
    return session.query(models.Post).all()
