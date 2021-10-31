"""
Flask app logic for P1M3
"""
# pylint: disable=no-member
# pylint: disable=too-few-public-methods
import os
import json
import random

import flask

from dotenv import load_dotenv, find_dotenv
from flask_login import (
    login_user,
    current_user,
    LoginManager,
    UserMixin,
    login_required,
)
from flask_sqlalchemy import SQLAlchemy

from genius import get_lyrics_link
from spotify import get_access_token, get_song_data


load_dotenv(find_dotenv())

app = flask.Flask(__name__, static_folder="./build/static")
# Point SQLAlchemy to your Heroku database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = b"I am a secret key"

db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    """
    Model for a) User rows in the DB and b) Flask Login object
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))

    def __repr__(self):
        """
        Determines what happens when we print an instance of the class
        """
        return f"<User {self.username}>"

    def get_username(self):
        """
        Getter for username attribute
        """
        return self.username


class Artist(db.Model):
    """
    Model for saved artists
    """

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        """
        Determines what happens when we print an instance of the class
        """
        return f"<Artist {self.artist_id}>"


db.create_all()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_name):
    """
    Required by flask_login
    """
    return User.query.get(user_name)


bp = flask.Blueprint("bp", __name__, template_folder="./build")


@bp.route("/index")
@login_required
def index():
    """
    Main page. Fetches song data and embeds it in the returned HTML. Returns
    dummy data if something goes wrong.
    """
    artists = Artist.query.filter_by(username=current_user.username).all()
    artist_ids = [a.artist_id for a in artists]
    has_artists_saved = len(artist_ids) > 0
    if has_artists_saved:
        artist_id = random.choice(artist_ids)

        # API calls
        access_token = get_access_token()
        (song_name, song_artist, song_image_url, preview_url) = get_song_data(
            artist_id, access_token
        )
        genius_url = get_lyrics_link(song_name)

    else:
        (song_name, song_artist, song_image_url, preview_url, genius_url) = (
            None,
            None,
            None,
            None,
            None,
        )

    data = json.dumps(
        {
            "username": current_user.username,
            "artist_ids": artist_ids,
            "has_artists_saved": has_artists_saved,
            "song_name": song_name,
            "song_artist": song_artist,
            "song_image_url": song_image_url,
            "preview_url": preview_url,
            "genius_url": genius_url,
        }
    )
    return flask.render_template(
        "index.html",
        data=data,
    )


app.register_blueprint(bp)


@app.route("/signup")
def signup():
    """
    Signup endpoint for GET requests
    """
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
    """
    Handler for signup form data
    """
    username = flask.request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        pass
    else:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    return flask.redirect(flask.url_for("login"))


@app.route("/login")
def login():
    """
    Login endpoint for GET requests
    """
    return flask.render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    """
    Handler for login form data
    """
    username = flask.request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        login_user(user)
        return flask.redirect(flask.url_for("bp.index"))

    return flask.jsonify({"status": 401, "reason": "Username or Password Error"})


@app.route("/save", methods=["POST"])
def save():
    """
    Receives JSON data from App.js, filters out invalid artist IDs, and
    updates the DB to contain all valid ones and nothing else.
    """
    artist_ids = flask.request.json.get("artist_ids")
    valid_ids = set()
    for artist_id in artist_ids:
        try:
            access_token = get_access_token()
            get_song_data(artist_id, access_token)
            valid_ids.add(artist_id)
        except KeyError:
            pass

    username = current_user.username
    update_db_ids_for_user(username, valid_ids)

    response = {"artist_ids": [a for a in artist_ids if a in valid_ids]}
    return flask.jsonify(response)


def update_db_ids_for_user(username, valid_ids):
    """
    Updates the DB so that only entries for valid_ids exist in it.
    @param username: the username of the current user
    @param valid_ids: a set of artist IDs that the DB should update itself
        to reflect
    """
    existing_ids = {
        v.artist_id for v in Artist.query.filter_by(username=username).all()
    }
    new_ids = valid_ids - existing_ids
    for new_id in new_ids:
        db.session.add(Artist(artist_id=new_id, username=username))
    if len(existing_ids - valid_ids) > 0:
        for artist in Artist.query.filter_by(username=username).filter(
            Artist.artist_id.notin_(valid_ids)
        ):
            db.session.delete(artist)
    db.session.commit()


@app.route("/")
def main():
    """
    Main page just reroutes to index or login depending on whether the
    user is authenticated
    """
    if current_user.is_authenticated:
        return flask.redirect(flask.url_for("bp.index"))
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    app.run(
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", "8081")),
    )
