from pathlib import Path
from requests.sessions import session
import base64
import requests
import time


SERVER_HOST = 'web'
# SERVER_HOST = '' # for local tests
SERVER_PORT = 5000
URL = 'http://' + SERVER_HOST
if SERVER_PORT != 80:
    URL += ':{}'.format(SERVER_PORT)
USERS_ENDPOINT = URL + '/users'
SIGNUP = URL + '/signup'
LOGIN = URL + '/login'
TEST_DATA_DIR = 'test_data'
GEN_STAT = URL + '/statistics/generate'

DATA_DIR = '/data'
# DATA_DIR = '' # for local tests

def ImageToString(fileName):
    img = open(fileName, "rb")
    return base64.b64encode(img.read()).decode()


user1 = {
    "username": "admin",
    "password": "admin_password"
}
user1WrongPass = user1.copy()
user1WrongPass["password"] = user1WrongPass["password"][::-1]

user2 = {
    "username": "super_admin",
    "password": "really_strong_password"
}


user1Info = {
    "name": "Cat",
    "email": "sample@gmail.com",
    "sex": "Male",
    "img": ImageToString(f'{TEST_DATA_DIR}/img.jpeg')
}

user1InfoUpdate = {
    "name": "Super Cute Cat",
    "email": "123@gmail.com",
}

user2Info = {
    "name": "Some Girl",
    "email": "123@gmail.com",
    "sex": "Female",
    "img": ImageToString(f'{TEST_DATA_DIR}/img2.jpeg')
}

def test_login_unknown_user():
    response = requests.post(LOGIN, json=user1)
    assert response.status_code == 401

def test_signup_user1():
    response = requests.post(SIGNUP, json=user1)
    assert response.status_code == 200

def test_signup_same_user_other_password():
    tmp = user1.copy()
    response = requests.post(SIGNUP, json=user1WrongPass)
    assert response.status_code == 400

def test_login():
    response = requests.post(LOGIN, json=user1)
    assert response.status_code == 200

def test_login_wrong_password():
    response = requests.post(LOGIN, json=user1WrongPass)
    assert response.status_code == 401

def test_post_text_without_login():
    response = requests.post(USERS_ENDPOINT, json=user1Info)
    assert response.status_code == 401

def test_post_user1_data():
    session = requests.Session()
    response = session.post(LOGIN, json=user1)
    assert response.status_code == 200
    response = session.post(USERS_ENDPOINT, json=user1Info)
    assert response.status_code == 200

def test_get_unknown_user_info():
    session = requests.Session()
    response = session.get(f'{USERS_ENDPOINT}/some_user')
    assert response.status_code == 404

def test_get_user1_info():
    session = requests.Session()
    response = session.get(f'{USERS_ENDPOINT}/{user1["username"]}')
    assert response.status_code == 200
    ans = response.json()
    assert ans[user1["username"]]["name"] == user1Info['name']
    assert ans[user1["username"]]["email"] == user1Info['email']
    assert ans[user1["username"]]["sex"] == user1Info['sex']
    assert ans[user1["username"]]["img"] == user1Info['img']

def test_change_user1_data():
    session = requests.Session()
    response = session.post(LOGIN, json=user1)
    assert response.status_code == 200
    response = session.post(USERS_ENDPOINT, json=user1InfoUpdate)
    assert response.status_code == 200

def test_get_user1_updated_info():
    session = requests.Session()
    response = session.get(f'{USERS_ENDPOINT}/{user1["username"]}')
    assert response.status_code == 200
    ans = response.json()
    assert ans[user1["username"]]["name"] == user1InfoUpdate['name']
    assert ans[user1["username"]]["email"] == user1InfoUpdate['email']
    assert ans[user1["username"]]["sex"] == user1Info['sex']
    assert ans[user1["username"]]["img"] == user1Info['img']

def test_signup_user2():
    response = requests.post(SIGNUP, json=user2)
    assert response.status_code == 200

def test_post_user2_data():
    session = requests.Session()
    response = session.post(LOGIN, json=user2)
    assert response.status_code == 200
    response = session.post(USERS_ENDPOINT, json=user2Info)
    assert response.status_code == 200

def test_get_user2_info():
    session = requests.Session()
    response = session.get(f'{USERS_ENDPOINT}/{user2["username"]}')
    assert response.status_code == 200
    ans = response.json()
    assert ans[user2["username"]]["name"] == user2Info['name']
    assert ans[user2["username"]]["email"] == user2Info['email']
    assert ans[user2["username"]]["sex"] == user2Info['sex']
    assert ans[user2["username"]]["img"] == user2Info['img']

def test_get_all_users_info():
    session = requests.Session()
    response = session.get(USERS_ENDPOINT)
    assert response.status_code == 200
    ans = response.json()
    assert ans[user1["username"]]["name"] == user1InfoUpdate['name']
    assert ans[user1["username"]]["email"] == user1InfoUpdate['email']
    assert ans[user1["username"]]["sex"] == user1Info['sex']
    assert ans[user1["username"]]["img"] == user1Info['img']
    assert ans[user2["username"]]["name"] == user2Info['name']
    assert ans[user2["username"]]["email"] == user2Info['email']
    assert ans[user2["username"]]["sex"] == user2Info['sex']
    assert ans[user2["username"]]["img"] == user2Info['img']

def test_delete_user2_without_login():
    session = requests.Session()
    response = session.delete(f'{USERS_ENDPOINT}/{user2["username"]}')
    assert response.status_code == 401

def test_delete_user2_with_login():
    session = requests.Session()
    response = session.post(LOGIN, json=user2)
    assert response.status_code == 200
    response = session.delete(f'{USERS_ENDPOINT}/{user2["username"]}')
    assert response.status_code == 200
    response = session.get(USERS_ENDPOINT)
    assert response.status_code == 200
    ans = response.json()
    assert (user2["username"] in ans) == False

def test_generate_user1_stat():
    session = requests.Session()
    response = session.get(f'{GEN_STAT}/{user1["username"]}')
    assert response.status_code == 200
    url = response.json()["url"]
    print(url, flush=True)
    time.sleep(2)
    response = session.get(f'{URL}/{url}')
    assert response.status_code == 200
