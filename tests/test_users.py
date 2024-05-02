from app import schemas
from app.config import settings
from jose import jwt
import pytest


def test_create_user(test_client):
    response = test_client.post(
        "/users/",
        json={"email": "tests@example.com", "password": "123456"})
    new_user = schemas.UserOut(**response.json())
    assert new_user.email == "tests@example.com"
    assert response.status_code == 201


def test_login_user(test_client, test_user):
    response = test_client.post(
        "/login/",
        data={"username": test_user['email'],
              "password": test_user['password']})
    login_response = schemas.Token(**response.json())
    payload = jwt.decode(login_response.access_token,
                         settings.secret_key,
                         algorithms=[settings.algorithm])
    id = payload.get('user_id')
    assert id == test_user['id']
    assert login_response.token_type == "bearer"
    assert response.status_code == 202


@pytest.mark.parametrize("email, password, status_code", [
    ("wrongemail@example.com", "123456", 403),
    ("tests@example.com", "wrongpassword", 403),
    ("wrongemail@example.com", "wrongpassword", 403),
    (None, "123456", 422),
    ("tests@example.com", None, 422)])
def test_login_invalidation(test_client, email, password, status_code):
    response = test_client.post(
        "/login/",
        data={"username": email,
              "password": password})
    assert response.status_code == status_code
