from flask import Flask

from .cli import gift_cli
from .view.gift import bp


def event_init(app: Flask):
    app.register_blueprint(bp)


def event_finish(app: Flask):
    app.cli.add_command(gift_cli)
