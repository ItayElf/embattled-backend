import os.path
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sock import Sock
from flask_sqlalchemy import SQLAlchemy

from web.hidden import JWT_SECRET_KEY

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = r"sqlite:///" + os.path.join("..", "main.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ECHO"] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)
sockets = Sock(app)
