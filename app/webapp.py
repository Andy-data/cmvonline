from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.urls import url_parse


server_bp = Blueprint('main', __name__)


@server_bp.route('/')
def index():
    return render_template("index.html", title='Home Page')




@server_bp.route('/login/')
def login():
    return redirect(url_for('main.index'))

