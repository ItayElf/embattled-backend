from web import *
from web.base import app


def main():
    """The main entrance of the program"""
    db.create_all()
    app.run(port=5555, debug=True)


if __name__ == '__main__':
    main()
