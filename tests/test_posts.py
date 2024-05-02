import pytest
from app import schemas


def test_get_all_posts(authorized_client, test_posts):
    response = authorized_client.get("/posts/")
    assert len(response.json()) == len(test_posts)
    assert response.status_code == 200


def test_unauthorized_user_get_one_posts(test_client, test_posts):
    response = test_client.get("/posts/{test_posts[0].id}")
    assert response.status_code == 401


def test_get_one_post_not_exist(authorized_client, test_posts):
    response = authorized_client.get("/posts/88888")
    assert response.status_code == 404


@pytest.mark.parametrize("title, content, published", [
    ("awesome title", "awesome content", True),
    ("favorite pizza", "i love pepperoni", False),
    ("tallest skyscrapers", "wahoo", True),
])
def test_create_post(authorized_client, test_user, test_posts,
                     title, content, published):
    response = authorized_client.post(
        "/posts/", json={"title": title, "content": content,
                         "published": published}
    )
    created_post = response.json()
    assert response.status_code == 201
    assert created_post["title"] == title
    assert created_post["content"] == content
    assert created_post["published"] == published
    assert created_post["owner_id"] == test_user["id"]


def test_unauthorized_user_create_post(test_client, test_posts):
    response = test_client.post(
        "/posts/", json={"title": "title", "content": "content",
                         "published": True}
    )
    assert response.status_code == 401


def test_unauthorized_user_delete_post(test_client, test_posts):
    response = test_client.delete("/posts/1")
    assert response.status_code == 401


def test_delete_post_success(authorized_client, test_posts):
    response = authorized_client.delete(f"/posts/{test_posts[0].id}")
    assert response.status_code == 204


def test_delete_post_non_exist(authorized_client, test_user, test_posts):
    response = authorized_client.delete("/posts/88888")
    assert response.status_code == 404


def test_delete_other_user_post(authorized_client, test_user, test_posts):
    response = authorized_client.delete(f"/posts/{test_posts[3].id}")
    assert response.status_code == 403


def test_update_post(authorized_client, test_user, test_posts):
    data = {
        "title": "updated title",
        "content": "updated content",
        "id": test_posts[0].id
    }
    response = authorized_client.put(f"/posts/{test_posts[0].id}", json=data)
    updated_post = schemas.Post(**response.json())
    assert response.status_code == 202
    assert updated_post.title == data["title"]
    assert updated_post.content == data["content"]


def test_update_other_user_post(authorized_client, test_user,
                                test_user_2, test_posts):
    data = {
        "title": "updated title",
        "content": "updated content",
        "id": test_posts[3].id
    }
    response = authorized_client.put(f"/posts/{test_posts[3].id}", json=data)
    assert response.status_code == 403


def test_unauthorized_user_update_post(test_client, test_posts):
    response = test_client.put(
        f"/posts/{test_posts[0].id}", json={"title": "updated title",
                                            "content": "updated content",
                                            "published": True}
    )
    assert response.status_code == 401


def test_update_post_non_exist(authorized_client, test_user, test_posts):
    data = {
        "title": "updated title",
        "content": "updated content",
        "id": test_posts[0].id
    }
    response = authorized_client.put("/posts/88888", json=data)
    assert response.status_code == 404
