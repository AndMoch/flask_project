import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class ThreadModel(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'threads'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String)