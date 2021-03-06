"""
Web application.
"""

import os

from flask import Flask, current_app, make_response

from coati.core import db
from coati.web import api


blueprints = [
    db,
    api
]


def send_index_response(path):
    """
    Send the standard 'index.html' file for our Angular application.
    """
    template = open(
        os.path.join(current_app.static_folder, 'index.html')
    ).read()

    return make_response(template)


def create_app(config):
    """
    Create a Flask app.
    :param config: config file.
    :return: WSGI application, a Flask object.
    """
    app = Flask(__name__,
                static_folder='frontend/static',
                static_url_path='/static',
                template_folder='templates')

    app.config.from_object(config)

    # Add URL routing to render the index
    app.add_url_rule('/', u'home', send_index_response, defaults={'path': ''})
    app.add_url_rule('/<path:path>', u'index', send_index_response)

    for bp in blueprints:
        try:
            init_app = bp.init_app
        except AttributeError:
            raise AttributeError('%r has no init_app' % (bp.__name__,))

        init_app(app)

    return app
