import base64
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from passlib.hash import bcrypt
import pymongo
import config
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from bson import json_util, ObjectId

application = Flask(__name__)
CORS(application)
application.config['JWT_SECRET_KEY'] = 'qrmenusecretkey'
jwt = JWTManager(application)

client = pymongo.MongoClient(config.mongo_string)
db = client['QRMenu']
users_collection = db['users']
categories_collection = db['categories']
reviews_collection = db['reviews']
dishes_collection = db['dishes']
demo_user_collection = db['demo_user']
demo_menu_collection = db['demo_menu']


@application.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    password_hash = bcrypt.hash(password)

    users_collection.insert_one({'username': username,
                                 'password': password_hash})

    return jsonify({'message': True}), 200


@application.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users_collection.find_one({'username': username})

    if user and bcrypt.verify(password, user['password']):
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        return jsonify({'access_token': access_token,
                        'refresh_token': refresh_token}), 200
    else:
        return jsonify({'message': False}), 401


@application.route('/update_user', methods=['POST'])
@jwt_required()
def update_user():
    data = request.form
    user = get_jwt_identity()
    existing_user = users_collection.find_one({'username': user})

    if existing_user:
        for field in ['type', 'schedule', 'contacts', 'useful_info', 'name', 'login', 'password', 'languages',
                      'currency', 'subscription']:
            if field in data:
                existing_user[field] = data[field]

        logo = request.files.get('logo')
        if logo:
            existing_user['logo'] = process_and_store_logo(logo)

        users_collection.replace_one({'username': user}, existing_user)
        return jsonify({'message': True}), 200

    else:
        return jsonify({'message': False}), 404


def process_and_store_logo(logo):
    try:
        # Read the image file as binary data
        image_data = logo.read()

        # Encode the binary image data as base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Return the base64 encoded image data for MongoDB storage
        return base64_image

    except Exception as e:
        # Handle any potential errors while processing the image
        print(f"Error processing image: {str(e)}")
        return None


@application.route('/user', methods=['GET'])
@jwt_required()
def user():
    user = get_jwt_identity()
    user = users_collection.find_one({'username': user})

    response = Response(
        json_util.dumps({
            'user': user
        }, ensure_ascii=False).encode('utf-8'),
        content_type='application/json;charset=utf-8'
    )

    return response, 200


@application.route('/add_category', methods=['POST'])
@jwt_required()
def add_category():
    data = request.form
    username = get_jwt_identity()
    name = data.get('name')
    subcategories = data.get('subcategories')
    description = data.get('description', None)
    photo = request.files.get('photo', None)
    if photo:
        photo = process_and_store_logo(photo)

    document = {'username': username,
                'name': name,
                'subcategories': subcategories,
                'description': description,
                'photo': photo}
    is_present = categories_collection.insert_one(document)
    if is_present is None:
        categories_collection.insert_one(document)
        return jsonify({'message': True}), 200
    else:
        return jsonify({'message': False}), 401


@application.route('/update_category', methods=['POST'])
@jwt_required()
def update_category():
    data = request.form
    category_id = data.get('category_id')

    existing_category = categories_collection.find_one({'_id': ObjectId(category_id)})

    if existing_category:
        for field in ['name', 'subcategories', 'description']:
            if field in data:
                existing_category[field] = data[field]

        photo = request.files.get('photo')
        if photo:
             existing_category['photo'] = process_and_store_logo(photo)

        categories_collection.replace_one({'_id': ObjectId(category_id)}, existing_category)
        return jsonify({'message': True}), 200

    else:
        return jsonify({'message': False}), 401


@application.route('/delete_category', methods=['POST'])
@jwt_required()
def delete_category():
    data = request.form
    category_id = data.get('category_id')

    category = categories_collection.find_one({'_id': ObjectId(category_id)})
    if category:
        categories_collection.delete_one(category)
        return jsonify({'message': True}), 200
    else:
        return jsonify({'message': False}), 401


@application.route('/categories', methods=['GET'])
@jwt_required()
def categories():
    user = get_jwt_identity()
    categories = categories_collection.find()

    response = Response(
        json_util.dumps({
            'categories': categories
        }, ensure_ascii=False).encode('utf-8'),
        content_type='application/json;charset=utf-8'
    )

    return response, 200


@application.route('/add_review', methods=['POST'])
@jwt_required()
def add_review():
    data = request.form
    dishes_rate = data.get('dishes_rate')
    service_rate = data.get('service_rate')
    comment = data.get('comment')
    phone = data.get('phone')
    email = data.get('email')
    name = data.get('name', None)
    username = get_jwt_identity()

    document = {'dishes_rate': dishes_rate,
                'service_rate': service_rate,
                'comment': comment,
                'phone': phone,
                'email': email,
                'name': name,
                'username': username}
    reviews_collection.insert_one(document)


@application.route('/reviews', methods=['GET'])
@jwt_required()
def reviews():
    user = get_jwt_identity()
    reviews = reviews_collection.find({'username': user})

    response = Response(
        json_util.dumps({
            'reviews': reviews
        }, ensure_ascii=False).encode('utf-8'),
        content_type='application/json;charset=utf-8'
    )

    return response, 200


@application.route('/add_dish', methods=['POST'])
@jwt_required()
def add_dish():
    data = request.form
    username = get_jwt_identity()
    name = data.get('name', None)
    price = data.get('price', None)
    description = data.get('description', None)
    weight = data.get('weight', None)
    category = data.get('category', None)
    subcategory = data.get('subcategory', None)
    takeaway = data.get('takeaway', None)
    here = data.get('here', None)
    units = data.get('units', None)
    label = data.get('label', None)
    photo = data.get('photo', None)
    if photo:
        photo = process_and_store_logo(photo)

    document = {
        'username': username,
        'name': name,
        'price': price,
        'description': description,
        'weight': weight,
        'category': category,
        'subcategory': subcategory,
        'takeaway': takeaway,
        'here': here,
        'units': units,
        'label': label,
        'photo': photo,
        'likes': 0
    }

    #dishes_collection.insert_one(document)
    demo_menu_collection.insert_one(document)
    return jsonify({'message': True}), 200


@application.route('/edit_likes', methods=['POST'])
@jwt_required()
def edit_likes():
    data = request.form
    type = data.get('type')
    user = get_jwt_identity()
    dish_id = data.get('dish_id')

    dish = dishes_collection.find_one({'_id': ObjectId(dish_id), 'username': user})

    if dish:
        if type == 'add':
            dishes_collection.find_one_and_update(dish, {'$set': {'likes': dish['likes'] + 1}})
        elif type == 'substract':
            dishes_collection.find_one_and_update(dish, {'$set': {'likes': dish['likes'] - 1}})

        return jsonify({'message': True}), 200
    else:
        return jsonify({'message': False}), 401


@application.route('/update_dish', methods=['POST'])
@jwt_required()
def update_dish():
    data = request.form
    dish_id = data.get('dish_id')

    existing_dish = dishes_collection.find_one({'_id': ObjectId(dish_id)})

    if existing_dish:
        for field in ['name', 'price', 'description', 'weight', 'category', 'subcategory', 'takeaway', 'here', 'units', 'label']:
            if field in data:
                existing_dish[field] = data[field]

        photo = request.files.get('photo')
        if photo:
            existing_dish['photo'] = process_and_store_logo(photo)

        dishes_collection.replace_one({'_id': ObjectId(dish_id)}, existing_dish)
        return jsonify({'message': True}), 200

    else:
        return jsonify({'message': False}), 401


@application.route('/delete_dish', methods=['POST'])
@jwt_required()
def delete_dish():
    data = request.form
    dish_id = data.get('dish_id')
    dishes_collection.delete_one({'_id': ObjectId(dish_id)})
    return jsonify({'message': False})


@application.route('/dishes', methods=['GET'])
@jwt_required()
def dishes():
    data = request.form
    username = get_jwt_identity()
    category = data.get('category')
    subcategory = data.get('subcategory')

    filter_criteria = {'username': username}
    if category:
        filter_criteria['category'] = category
    if subcategory:
        filter_criteria['subcategory'] = subcategory

    dishes = dishes_collection.find()

    response = Response(
        json_util.dumps({
            'dishes': dishes
        }, ensure_ascii=False).encode('utf-8'),
        content_type='application/json;charset=utf-8'
    )

    return response, 200


@application.route('/demo_user', methods=['GET'])
def demo_user():
    data = demo_user_collection.find()

    response = Response(
        json_util.dumps({
            'user': data
        }, ensure_ascii=False).encode('utf-8'),
        content_type='application/json;charset=utf-8'
    )

    return response, 200


@application.route('/demo_menu', methods=['GET'])
def demo_menu():
    data = list(demo_menu_collection.find())

    response = Response(
        json_util.dumps(data, ensure_ascii=False).encode('utf-8'),
        content_type='application/json;charset=utf-8'
    )

    return response, 200


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8000)
