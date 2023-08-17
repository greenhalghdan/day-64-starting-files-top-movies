from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///topmovies.db"
db = SQLAlchemy()
db.init_app(app)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.String, nullable=False)
    rank = db.Column(db.Integer)
    img_url = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()
    db.session.commit()

class MyForm(FlaskForm):
    rating = FloatField(label='Rating', validators=[DataRequired(message='Plese enter a rating')])
    review = StringField(label="Review", validators=[DataRequired(message='Plese enter a review')])
    submit = SubmitField(label="Update", )

class AddMovie(FlaskForm):
    moviename = StringField(label="Movie Name", validators=[DataRequired(message='Plese enter a review')])
    submit = SubmitField(label="Add", )

with app.app_context():
    result = db.session.execute(db.select(Movies).order_by(Movies.title)).scalars()
    all_movie = result.all()


@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movies).order_by(Movies.rating)).scalars()
        all_movie = result.all()

        i = len(all_movie)
        for movie in  all_movie:
            movie = db.session.execute(db.select(Movies).where(Movies.id == movie.id)).scalar()
            movie.rank = i
            db.session.commit()
            i -= 1

        result = db.session.execute(db.select(Movies).order_by(Movies.rating)).scalars()
        all_movie = result.all()
    return render_template("index.html", movies=all_movie)


@app.route("/edit/<int:movieid>", methods=["GET", "POST"])
def edit(movieid):
    form = MyForm()
    if request.method == "POST":
        print(movieid)
        movie = db.session.execute(db.select(Movies).where(Movies.id == movieid)).scalar()
        movie.rating = request.form["rating"]
        movie.review = request.form["review"]
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete/<int:movieid>", methods=["GET", "POST"])
def delete(movieid):
    print(movieid)
    movie = db.session.execute(db.select(Movies).where(Movies.id == movieid)).scalar()
    print(movie)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if request.method == "POST":
        import requests

        url = "https://api.themoviedb.org/3/search/movie?"

        params = {
            "query": request.form["moviename"]
        }

        headers = {
            "accept": "application/json",
            "Authorization": os.environ.get("token")
        }

        data = requests.get(url, params=params, headers=headers)

        data = data.json()
        movie_data = data["results"]
        return render_template("select.html", data=movie_data)
    return render_template("add.html", form=form)

@app.route("/newfilm", methods=["GET", "POST"])
def newfilm():
    film_id = request.args.get('id')
    if request.method == "POST":
        with app.app_context():
            import requests

            url = f"https://api.themoviedb.org/3/movie/{film_id}?language=en-US"

            headers = {
                "accept": "application/json",
                "Authorization": os.environ.get("token")
            }

            response = requests.get(url, headers=headers)
            data = response.json()
            new_movie = Movies(
                                title=data["original_title"],
                                year=data["release_date"],
                                description=data['overview'],
                                rating=request.form["rating"],
                                review=request.form["review"],
                                img_url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
                              )
            db.session.add(new_movie)
            db.session.commit()
            print(f"https://image.tmdb.org/t/p/original{data['backdrop_path']}")
        return redirect(url_for('home'))

    form = MyForm()
    return render_template("edit.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
