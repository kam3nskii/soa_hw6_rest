from config import DATA_DIR, USERS_ENDPOINT, GEN_STAT_ENDPOINT, VIEW_STAT_ENDPOINT
from flask import Flask, request, send_file
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
from pathlib import Path
import base64
import json
import pika
import shutil
import time

RETRY_CNT = 10


# для авторизации я вдохновлялся примером использования flask_login
# https://github.com/shekhargulati/flask-login-example/blob/master/flasklogin.py


class User(UserMixin):
    def __init__(self , username , password , id , active=True):
        self.id = id
        self.username = username
        self.password = password
        self.active = active

    def get_id(self):
        return self.id

    def is_active(self):
        return self.active


class UseresDB:
    def __init__(self):
        self.users = dict()
        self.users_id_dict = dict()
        self.identifier = 0

    def saveUser(self, user):
        self.users_id_dict.setdefault(user.id, user)
        self.users.setdefault(user.username, user)

    def getUserByUsername(self, username):
        return self.users.get(username, None)

    def getUserById(self, userid):
        return self.users_id_dict.get(userid, None)

    def nextIndex(self):
        self.identifier += 1
        return str(self.identifier)


def StringToImage(str, fileName):
    base64Img = str.encode()
    file = open(fileName, 'wb')
    file.write(base64.b64decode((base64Img)))
    file.close()


def create_app() -> Flask:
    app = Flask(__name__)

    app.textsIds = 0
    app.usersDB = UseresDB()

    app.connection = None
    app.channel = None
    app.wasError = True

    app.config.update(
        SECRET_KEY = 'secret_key'
    )

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(userid):
        return app.usersDB.getUserById(userid)

    @app.route('/signup', methods=['POST'])
    def signup():
        data = request.get_json(force=True)
        username = data['username']
        password = data['password']
        registeredUser = app.usersDB.getUserByUsername(username)
        if registeredUser is None:
            newUser = User(username, password, app.usersDB.nextIndex())
            app.usersDB.saveUser(newUser)
            return {}
        else:
            return {}, 400

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json(force=True)
        username = data['username']
        password = data['password']
        registeredUser = app.usersDB.getUserByUsername(username)
        if registeredUser is None:
            return {}, 401
        if registeredUser.password == password:
            login_user(registeredUser)
            return {}
        return {}, 401

    @app.route(USERS_ENDPOINT, methods=['POST'])
    @login_required
    def save_user_info():
        newUserInfo = request.get_json(force=True)
        currUser = current_user.username
        userFolder = f'{DATA_DIR}/{currUser}'
        folder = Path(userFolder)
        textFile = Path(f'{userFolder}/info.json')
        if not folder.exists():
            folder.mkdir()
            textFile.touch()
            textFile.write_text('{}')
        oldUserInfo = json.loads(textFile.read_text())

        for key in {"name", "email", "sex", "img"}:
            if key in newUserInfo:
                oldUserInfo[key] = newUserInfo[key]
                if key == "img":
                    StringToImage(newUserInfo[key], f'{userFolder}/img.jpeg')

        textFile.write_text(json.dumps(oldUserInfo, indent=4))

        # stat file for test
        statFile = Path(f'{userFolder}/stat.json')
        statFile.write_text('{"sessions": 42,"wins": 31, "losses": 11, "play_time": "01:53:21"}')

        return {}

    @app.route(f'{USERS_ENDPOINT}/<string:username>', methods=['DELETE'])
    @login_required
    def delete_user_info(username):
        currUser = current_user.username
        if currUser != username:
            return {}, 401
        userFolder = f'{DATA_DIR}/{username}'
        folder = Path(userFolder)
        if not folder.exists():
            return {}, 404
        shutil.rmtree(userFolder)
        return {}

    @app.route(USERS_ENDPOINT, methods=['GET'])
    def get_users_info():
        usersFolder = Path(DATA_DIR)
        answer = {}
        for userFolder in usersFolder.iterdir():
            textFile = Path(f'{userFolder}/info.json')
            answer[userFolder.name] = json.loads(textFile.read_text())
        return answer

    @app.route(f'{USERS_ENDPOINT}/<string:username>', methods=['GET'])
    def get_user_info(username):
        userFolder = f'{DATA_DIR}/{username}'
        folder = Path(userFolder)
        if not folder.exists():
            return {}, 404
        textFile = Path(f'{userFolder}/info.json')
        return {f'{username}': json.loads(textFile.read_text())}

    @app.route(f'{GEN_STAT_ENDPOINT}/<string:username>', methods=['GET'])
    def generate_user_stat(username):
        message = f"{username} {DATA_DIR}"

        if app.wasError:
            for i in range(RETRY_CNT):
                try:
                    # app.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) # for local tests
                    app.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq')) # for docker compose
                    app.channel = app.connection.channel()
                    app.channel.queue_declare(queue='task_queue', durable=True)
                    app.channel.confirm_delivery()
                    print('Got connection to task_queue')
                    app.wasError = False
                    break
                except Exception as e:
                    time.sleep(1)
                    print('Waiting for connection to task_queue')
        if app.wasError:
            return {'error': 'No connection to task_queue'}, 504

        try:
            app.channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2, # persistent message
                )
            )
            app.wasError = False
            return {"url": f"statistics/view/{username}"}
        except Exception as e:
            app.wasError = True
            return {'error': 'Message not delivered to task_queue'}, 504

    @app.route(f'{VIEW_STAT_ENDPOINT}/<string:username>', methods=['GET'])
    def get_user_stat(username):
        statFilePath = f'{DATA_DIR}/{username}/{username}.pdf'
        file = Path(statFilePath)
        if not file.exists():
            return {}, 404
        return send_file(statFilePath, as_attachment=True)

    return app


app = create_app()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
