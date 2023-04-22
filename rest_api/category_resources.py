from flask import jsonify
from flask_restful import abort, Resource, reqparse

from data import db_session
from data.categories import Category


parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('user_id', required=True, type=int)


class CategoryResource(Resource):
    def get(self, cat_id):
        abort_if_category_not_found(cat_id)
        session = db_session.create_session()
        category = session.query(Category).get(cat_id)
        return jsonify({'category': category.to_dict(
            only=('title', 'user_id'))})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        category = Category(
            title=args['title'],
            user_id=args['user_id']
        )
        session.add(category)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, cat_id):
        args = parser.parse_args()
        session = db_session.create_session()
        category = session.query(Category).get(cat_id)
        if args['title']:
            category.title = args['title']
        session.commit()
        return jsonify({'status': 'success'})

    def delete(self, cat_id):
        abort_if_category_not_found(cat_id)
        session = db_session.create_session()
        category = session.query(Category).get(cat_id)
        session.delete(category)
        session.commit()
        return jsonify({'status': 'success'})


class CategoryListResource(Resource):
    def get(self):
        session = db_session.create_session()
        categories = session.query(Category).all()
        return jsonify({'categories': [item.to_dict(
            only=('title', 'user_id')) for item in categories]})


def abort_if_category_not_found(cat_id):
    session = db_session.create_session()
    category = session.query(Category).get(cat_id)
    if not category:
        abort(404, message=f"Category {cat_id} not found")