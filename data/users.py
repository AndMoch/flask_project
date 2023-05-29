from time import time

import sqlalchemy
import datetime
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
import jwt
from dotenv import dotenv_values
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    login = sqlalchemy.Column(sqlalchemy.String,
                              unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                      default=datetime.datetime.now)
    context_menu_enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    buttons_enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    notifications_enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    businesses = orm.relationship("Business", back_populates="user")
    categories = orm.relationship("Category", back_populates="user")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            dotenv_values('.env')['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(token, dotenv_values('.env')['SECRET_KEY'],
                                 algorithms=['HS256'])['reset_password']
        except:
            return
        return user_id