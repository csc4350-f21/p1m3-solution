import flask
from flask_login.utils import login_required
import requests
import os
import json

import random
import base64
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from genius import get_lyrics_link
from spotify import get_access_token, get_song_data

from flask_login import login_user, current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy

app = flask.Flask(__name__, static_folder="./build/static")
# Point SQLAlchemy to your Heroku database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

from flask_login import UserMixin

db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))

    def __repr__(self):
        return f"<User {self.username}>"

    def get_username(self):
        return self.username


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f"<Artist {self.artist_id}>"


db.create_all()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_name):
    return User.query.get(user_name)


def get_access_token():
    auth = base64.standard_b64encode(
        bytes(
            f"{os.getenv('SPOTIFY_CLIENT_ID')}:{os.getenv('SPOTIFY_CLIENT_SECRET')}",
            "utf-8",
        )
    ).decode("utf-8")
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth}"},
        data={"grant_type": "client_credentials"},
    )
    json_response = response.json()
    return json_response["access_token"]


bp = flask.Blueprint("bp", __name__, template_folder="./build")


@bp.route("/index")
@login_required
def index():
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
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
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
    return flask.render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    username = flask.request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        login_user(user)
        return flask.redirect(flask.url_for("bp.index"))

    else:
        return flask.jsonify({"status": 401, "reason": "Username or Password Error"})


@app.route("/save", methods=["POST"])
def save():
    artist_ids = flask.request.json.get("artist_ids")
    valid_ids = set()
    for artist_id in artist_ids:
        try:
            access_token = get_access_token()
            get_song_data(artist_id, access_token)
            valid_ids.add(artist_id)
        except Exception:
            pass

    username = current_user.username

    response = {"artist_ids": [a for a in artist_ids if a in valid_ids]}
    return flask.jsonify(response)


def update_db_ids_for_user(username, valid_ids):
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
    if current_user.is_authenticated:
        return flask.redirect(flask.url_for("bp.index"))
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    app.run(
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", 8081)),
    )
