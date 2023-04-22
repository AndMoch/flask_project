import datetime

from flask import jsonify
from flask_restful import abort, Resource, reqparse

from data import db_session
from data.businesses import Business

parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('priority', required=True, type=int)
parser.add_argument('start_date', required=True, type=datetime.datetime)
parser.add_argument('end_date', required=True, type=datetime.datetime)
parser.add_argument('status', required=True)
parser.add_argument('user_id', required=True, type=int)
parser.add_argument('category_id', required=True, type=int)


class BusinessResource(Resource):
    def get(self, bus_id):
        abort_if_business_not_found(bus_id)
        session = db_session.create_session()
        business = session.query(Business).get(bus_id)
        return jsonify({'business': business.to_dict(
            only=('title', 'content', 'user_id', 'is_private', 'user_id', 'is_private'))})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        business = Business(
            title=args['title'],
            priority=args['priority'],
            category_id=args['category_id'],
            start_date=args['start_date'],
            end_date=args['end_date'],
            status=args['status'],
            user_id=args['user_id']
        )
        session.add(business)
        session.commit()
        return jsonify({'status': 'success'})

    def put(self, bus_id):
        abort_if_business_not_found(bus_id)
        args = parser.parse_args()
        session = db_session.create_session()
        business = session.query(Business).get(bus_id)
        if args['title']:
            business.title = args['title']
        if args['priority']:
            business.priority = args['priority']
        if args['category_id']:
            business.category_id = args['category_id']
        if args['end_date']:
            business.end_date = args['end_date']
        if args['status']:
            business.status = args['status']
        session.commit()
        return jsonify({'status': 'success'})

    def delete(self, bus_id):
        abort_if_business_not_found(bus_id)
        session = db_session.create_session()
        business = session.query(Business).get(bus_id)
        session.delete(business)
        session.commit()
        return jsonify({'status': 'success'})


class BusinessesListResource(Resource):
    def get(self):
        session = db_session.create_session()
        businesses = session.query(Business).all()
        return jsonify({'businesses': [item.to_dict(
            only=('title', 'content', 'user.name')) for item in businesses]})


def abort_if_business_not_found(bus_id):
    session = db_session.create_session()
    business = session.query(Business).get(bus_id)
    if not business:
        abort(404, message=f"Business {bus_id} not found")