from flask import Flask, jsonify, request, g, render_template
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import bcrypt
import jwt
import datetime
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from bson import json_util, ObjectId
from models import Movie, Show, Theater

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'iam_admin'
app.config['MONGO_URI'] = os.getenv('MONGO_URL')
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Hash the password with bcrypt before saving it to the database


def hash_password(password):
    return bcrypt.generate_password_hash(password.encode('utf-8'), rounds=5)


@app.route('/signup', methods=['POST'])
def create_user():
    user = request.get_json()
    if 'name' not in user or 'email' not in user or 'password' not in user:
        return jsonify({'message': 'Name, email, and password are required fields'}), 400

    # Hash the password before saving it to the database
    hashed_password = hash_password(user['password'])
    new_user = {
        'name': user['name'],
        'email': user['email'],
        'password': hashed_password,
        'gender': user.get('gender'),
        'membership': user.get('membership'),
        # Default to 'user' if 'type' is not provided
        'type': user.get('type'),
    }
    result = mongo.db.users.insert_one(new_user)
    return jsonify({'message': 'User created successfully', 'user_id': str(result.inserted_id)})

# Getting all users


@app.route('/users', methods=['GET'])
def get_users():
    users = mongo.db.users.find()
    user_list = []
    for user in users:
        user_dict = {
            '_id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'password': user['password'],
            'gender': user['gender'],
            'membership': user['membership'],
            'type': user['type'],
        }
        user_list.append(user_dict)
    return json_util.dumps(user_list)


# Deleting a user
@app.route('/user/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Find the user document by its unique ID
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if user:
        # Delete the user from the database
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        return jsonify({'message': f'User with ID {user_id} deleted successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Updating a user


@app.route('/user/<string:user_id>', methods=['PUT'])
def update_user(user_id):
    # Retrieve the updated data from the request
    updated_data = request.get_json()
    # Find the user document by its unique ID
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if user:
        # Update the user document with the new data
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {
                                  '$set': updated_data})
        return jsonify({'message': f'User with ID {user_id} updated successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# login as a user


@app.route("/user", methods=["GET"])
def login():
    # Retrieve the data from the request
    email = request.args.get('email')
    password = request.args.get('password')

    # Find the user document by username
    user = mongo.db.users.find_one({"email": email})
    # print(user)
    if user and bcrypt.check_password_hash(user["password"], password):
        return json_util.dumps(user), 200
    else:
        return jsonify({"Error": "Invalid username or password"}), 201

# Login as admin


@app.route("/admin", methods=["GET"])
def adminLogin():
    # Retrieve the data from the request
    email = request.args.get('email')
    password = request.args.get('password')

    # Find the user document by username
    user = mongo.db.users.find_one({"email": email})
    # print(user)
    if user and bcrypt.check_password_hash(user["password"], password):
        return json_util.dumps(user), 200
    else:
        return jsonify({"Error": "Invalid username or password"}), 201


# Posting a Movie

@app.route('/movies', methods=['POST'])
def create_movie():
    movie_data = request.get_json()
    movie = Movie(**movie_data)
    movie.save()
    return jsonify({'message': 'Movie created successfully', 'movie_id': str(movie.id)}), 200


@app.route('/movies/<string:movie_id>', methods=['GET'])
def get_movie_by_id(movie_id):
    movie = Movie.objects(id=movie_id).first()
    if not movie:
        return jsonify({"message": f"Movie not found with ID {movie_id}"}), 404
    movie_data = {
        "id": str(movie.id),
        "title": movie.title,
        "description": movie.description,
        "duration": movie.duration,
        "genre": movie.genre,
        "language": movie.language,
        "release_date": movie.release_date,
        "image_cover": movie.image_cover,
        "rating": movie.rating
    }

    return jsonify(movie_data), 200

# Get all Movies data


@app.route('/movies', methods=['GET'])
def get_movies():
    sort_by = request.args.get('sort_by', 'title')  # Default sort by release_date
    language = request.args.get('language') # Language filter (optional)
    sort_order = request.args.get('sort_order', 'asc')
    page = int(request.args.get('page', 1)) - 1  # Default page 1
    limit = int(request.args.get('limit', 10))  # Default limit 10

    # Calculate skip value for pagination
    skip = page * limit
    if sort_order not in ('asc', 'desc'):
        return jsonify({"message": "Invalid sort_order parameter. Use 'asc' or 'desc'."}), 400
    
    sort_direction = '-' if sort_order == 'desc' else ''
    # Query and sort movies
    filter_query = {}
    if language:
        filter_query['language'] = language

    # Query and sort movies with the optional filter
    movies = Movie.objects(**filter_query).order_by(f"{sort_direction}{sort_by}").skip(skip).limit(limit)

    movie_list = [movie.to_mongo().to_dict() for movie in movies]
    for movie in movie_list:
        movie['_id'] = str(movie['_id'])
    return json_util.dumps(movie_list), 200

# Delete a specific Movies data


@app.route('/movies/<string:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    # Find the movie by its ID
    movie = Movie.objects(id=movie_id).first()
    if not movie:
        return jsonify({"message": f"Movie not found with ID {movie_id}"}), 404
    # Delete the movie
    movie.delete()
    return jsonify({"message": "Movie deleted successfully with ID {movie_id}"}), 200

# Update a specific Movies data


@app.route('/movies/<string:movie_id>', methods=['PATCH'])
def update_movie(movie_id):
    # Find the movie by its ID
    movie = Movie.objects(id=movie_id).first()
    if not movie:
        return jsonify({"message": f"Movie not found with ID {movie_id}"}), 404

    # Get the updated data from the request body
    updated_data = request.get_json()

    # Update the movie fields
    movie.title = updated_data.get('title', movie.title)
    movie.description = updated_data.get('description', movie.description)
    movie.duration = updated_data.get('duration', movie.duration)
    movie.genre = updated_data.get('genre', movie.genre)
    movie.language = updated_data.get('language', movie.language)
    movie.release_date = updated_data.get('release_date', movie.release_date)
    movie.image_cover = updated_data.get('image', movie.image_cover)
    movie.rating = updated_data.get('rating', movie.rating)

    # Save the changes to the database
    movie.save()
    return json_util.dumps({"message": "Movie updated successfully", "movie_id": movie_id}), 200


# Posting a Theater
@app.route('/theaters', methods=['POST'])
def create_theater():
    theater_data = request.get_json()
    theater = Theater(**theater_data)
    theater.save()
    return jsonify({'message': 'Theater created successfully', 'theater_id': str(theater.id)}), 200

# Get all theaters data

@app.route('/theaters', methods=['GET'])
def get_theaters():
    theaters = Theater.objects()
    
    # Convert MongoDB documents to dictionaries
    theaters_list = [theater.to_mongo().to_dict() for theater in theaters]
    # Convert the '_id' field to string format in each theater
    for theater in theaters_list:
        theater['_id'] = str(theater['_id'])
    
    return json_util.dumps(theaters_list), 200

# get a theater by id
@app.route('/theaters/<string:theater_id>', methods=['GET'])
def get_theater_by_id(theater_id):
    theater = Theater.objects(id=theater_id).first()
    if not theater:
        return jsonify({"message": f"Movie not found with ID {theater_id}"}), 404
    theater_data = {
        "id": str(theater.id),
        "name": theater.name,
        "city": theater.city,
        "address": theater.address,
        "capacity": theater.capacity,
        "state": theater.state,
    }

    return jsonify(theater_data), 200


@app.route('/theaters/<string:theater_id>', methods=['PATCH'])
def update_theater(theater_id):
    # Find the theater by its ID
    theater = Theater.objects(id=theater_id).first()
    print(theater_id)
    if not theater:
        return jsonify({"message": f"Theater not found with ID {theater_id}"}), 404

    # Get the updated data from the request body
    updated_data = request.get_json()
    # Update the theater fields
    theater.name = updated_data.get('name', theater.name)
    theater.address = updated_data.get('address', theater.address)
    theater.city = updated_data.get('city', theater.city)
    theater.state = updated_data.get('state', theater.state)
    theater.capacity = updated_data.get('capacity', theater.capacity)

    # Save the changes to the database
    theater.save()
    return jsonify({"message": "Theater updated successfully", "theaterID": theater_id}), 200

# Delete a specific theaters data


@app.route('/theaters/<string:theater_id>', methods=['DELETE'])
def delete_theater(theater_id):
    # Find the theater by its ID
    theater = Theater.objects(id=theater_id).first()
    if not theater:
        return jsonify({"message": f"Theater with ID {theater_id} is not found"}), 404
    # Delete the theater
    theater.delete()
    return jsonify({"message": f"Show deleted successfully with ID {theater_id}"}), 200


# Posting A show data
@app.route('/shows', methods=['POST'])
def create_show():
    show_data = request.get_json()
    # Get the Movie and Theater IDs from the request JSON
    movie_id = show_data.get('movie_id')
    theater_id = show_data.get('theater_id')
    # Find the Movie and Theater documents by their IDs
    movie = Movie.objects(id=movie_id).first()
    theater = Theater.objects(id=theater_id).first()
    if not movie or not theater:
        return jsonify({"message": "Invalid Movie or Theater ID"}), 400
    # Create a new Show document with the provided data
    show = Show(movie_id=movie, theater_id=theater, show_timing=show_data.get(
        'show_timing', []), category=show_data.get('category', []), dates=show_data.get('dates', []))
    show.save()

    return jsonify({"message": "Show created successfully", "show_id": str(show.id)}), 201



# Get all shows data
@app.route('/shows', methods=['GET'])
def get_shows():
    shows = Show.objects()
    # Convert MongoDB documents to dictionaries
    show_list = [show.to_mongo().to_dict() for show in shows]
    for show in show_list:
        show['_id']=str(show['_id'])
        show['movie_id']=str(show['movie_id'])
        show['theater_id']=str(show['theater_id'])
    return json_util.dumps(show_list), 200

# get a show by id
@app.route('/shows/<string:show_id>', methods=['GET'])
def get_show_by_id(show_id):
    show = Show.objects(id=show_id).first()
    if not show:
        return jsonify({"message": f"Show not found with ID {show_id}"}), 404

    shows_data = {
        "id":str(show.id),
        "movie_id": str(show.movie_id.id),
        "theater_id": str(show.theater_id.id),
        "show_timing": show.show_timing,
        "category": show.category
    }

    return jsonify(shows_data), 200


# get a show by movie_id
@app.route('/shows/movie/<string:movie_id>', methods=['GET'])
def get_show_by_movie_id(movie_id):
    show = Show.objects(movie_id=movie_id).first()
    if not show:
        return jsonify({"message": f"Show not found with ID {movie_id}"}), 404

    shows_data = {
        "id":str(show.id),
        "movie_id": str(show.movie_id.id),
        "theater_id": str(show.theater_id.id),
        "show_timing": show.show_timing,
        "category": show.category
    }

    return jsonify(shows_data), 200

# Update the specific show data


@app.route('/shows/<string:show_id>', methods=['PATCH'])
def update_show(show_id):
    show_data = request.get_json()

    # Find the show by its ID
    show = Show.objects(id=show_id).first()
    if not show:
        return jsonify({"message": "Show not found"}), 404

    # Update the show with the new data
    show.movie_id = show_data.get('movie_id', show.movie_id)
    show.theater_id = show_data.get('theater_id', show.theater_id)
    show.show_timing = show_data.get('show_timing', show.show_timing)
    show.category = show_data.get('category', show.category)
    show.dates = show_data.get('dates', show.dates)
    show.save()

    return jsonify({"message": f"Show updated successfully for ID - {show_id}"}), 200

# Delete the specific show data

@app.route('/shows/<string:show_id>', methods=['DELETE'])
def delete_show(show_id):
    # Find the show by its ID
    show = Show.objects(id=show_id).first()
    if not show:
        return jsonify({"message": f"Show with ID {show_id} is not found"}), 404
    # Delete the show
    show.delete()
    return jsonify({"message": f"Show deleted successfully with ID {show_id}"}), 200


# Events and participants
class Event:
    def __init__(self, title, description, date, time,poster):
        self.title = title
        self.description = description
        self.date = date
        self.time = time
        self.poster = poster

@app.route('/events', methods=['GET'])
def get_events():
    # Get query parameters for sorting and pagination
    sort_by = request.args.get('sort_by', 'title')  # Default to sorting by title
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # Determine the skip value for pagination
    skip = (page - 1) * limit

    # Query the events collection with sorting and pagination options
    events = mongo.db.events.find().sort(sort_by, 1).skip(skip).limit(limit)

    event_list = []
    for event in events:
        event_data = {
            'id': str(event['_id']),
            'title': event['title'],
            'description': event['description'],
            'date': event['date'],
            'time': event['time'],
            'poster': event['poster']
        }
        event_list.append(event_data)

    return jsonify(event_list)

@app.route('/events', methods=['POST'])
def create_event():
    data = request.get_json()
    event = Event(
        title=data['title'],
        description=data['description'],
        date=data['date'],
        time=data['time'],
        poster=data['poster']
    )
    result = mongo.db.events.insert_one(event.__dict__)
    return jsonify({'message': 'Event created successfully', 'event_id': str(result.inserted_id)})

@app.route('/events/<event_id>', methods=['GET'])
def get_event(event_id):
    event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
    if event:
        event_dict = {
            'id': str(event['_id']),
            'title': event['title'],
            'description': event['description'],
            'date': event['date'],
            'time': event['time'],
            'poster': event.get('poster', '')
        }
        return jsonify(event_dict)
    else:
        return jsonify({'message': 'Event not found'}), 404

@app.route('/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    updated_event = {
        'title': data.get('title'),
        'description': data.get('description'),
        'date': data.get('date'),
        'time': data.get('time'),
        'poster':data.get('poster')
    }
    result = mongo.db.events.update_one({'_id': ObjectId(event_id)}, {'$set': updated_event})
    if result.modified_count > 0:
        return jsonify({'message': 'Event updated successfully'})
    else:
        return jsonify({'message': 'Event not found'}), 404

@app.route('/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    result = mongo.db.events.delete_one({'_id': ObjectId(event_id)})
    if result.deleted_count > 0:
        return jsonify({'message': 'Event deleted successfully'})
    else:
        return jsonify({'message': 'Event not found'}), 404



class Participant:
    def __init__(self, name, email):
        self.name = name
        self.email = email

@app.route('/events/<event_id>/participants', methods=['GET'])
def get_participants(event_id):
    event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
    if event:
        participants = mongo.db.events.get('participants', [])
        return jsonify(participants)
    else:
        return jsonify({'message': 'Event not found'}), 404

@app.route('/events/<event_id>/participants', methods=['POST'])
def add_participant(event_id):
    data = request.get_json()
    participant = Participant(name=data.get('name'), email=data.get('email'))
    mongo.db.events.update_one({'_id': ObjectId(event_id)}, {'$push': {'participants': participant.__dict__}})
    return jsonify({'message': 'Participant added to the event successfully'})

@app.route('/events/<event_id>/participants', methods=['DELETE'])
def remove_participant(event_id):
    data = request.get_json()
    if 'email' not in data:
        return jsonify({'message': 'Participant email not provided'}), 400

    event = mongo.db.events.find_one({'_id': ObjectId(event_id)})
    if event:
        participants = event.get('participants', [])
        for participant in participants:
            if participant.get('email') == data['email']:
                participants.remove(participant)
                mongo.db.events.update_one({'_id': ObjectId(event_id)}, {'$set': {'participants': participants}})
                return jsonify({'message': 'Participant removed from the event successfully'})
        return jsonify({'message': 'Participant not found in the event'}), 404
    else:
        return jsonify({'message': 'Event not found'}), 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
