import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from mvc.model import User, db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif User.query.filter_by(username=username).first() is not None:
            error = "User {} is already registered.".format(username)

        if error is None:
            user = User(username=username, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash(f"a user [{user.username}] was successfully registered")
            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        user = User.query.filter_by(username=username).first()
        if user is None:
            error = "Incorrect username"
        elif not check_password_hash(user.password, password):
            error = "Incorrect password"

        # set user_id in session upon successful login
        if error is None:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("todos.home"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.index"))


def login_required(view):
    """A decorator to apply to views that needs user to be logged in.
    Returns a new view function that wraps the original view.
    The new view checks if a user is loaded otherwise redirects to login.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
