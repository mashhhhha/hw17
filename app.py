from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

# creating of app and configs
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 4}

# creating of database
db = SQLAlchemy(app)


# descriotion of models
class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# creating schemas
class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class MovieSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    rating = fields.Float()
    genre = fields.Nested(GenreSchema, only=['name'])
    director = fields.Pluck(field_name='name', nested=DirectorSchema)


# creating instances of schemas

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)

director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)


# creating of namespaces
movie_ns = api.namespace('movies')
genre_ns = api.namespace('genres')
director_ns = api.namespace('directors')


# creating the view for movies . This view returns all movie list and with query params
@movie_ns.route('/')
class MoviesView(Resource):
    def get(self):
        all_movies = Movie.query.all()
        query_director = request.args.get('director_id')
        query_genre = request.args.get('genre_id')

        if query_director:
            all_movies = db.session.query(Movie).filter(Movie.director_id == query_director).all()

        if query_genre:
            all_movies = db.session.query(Movie).filter(Movie.genre_id == query_genre).all()

        if query_director and query_genre:
            all_movies = db.session.query(Movie).filter(Movie.director_id == query_director,
                                                        Movie.genre_id == query_genre).all()

        if len(all_movies) == 0:
            return '', 404

        return movies_schema.dump(all_movies)

    def post(self):
        req_json = request.json

        if not req_json:
            return '', 404

        new_movie = Movie(**req_json)

        with db.session.begin():
            db.session.add(new_movie)

        return '', 201


# creating the view for current movie
@movie_ns.route('/<int:pk>')
class MovieView(Resource):
    def get(self, pk):
        try:
            current_movie = Movie.query.get(pk)

            return movie_schema.dump(current_movie)

        except Exception as e:
            return f'{e}', 404


if __name__ == '__main__':
    app.run(debug=True)