from app import cli, create_app, db
from app.models import Notification, Post, User

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Post": Post, "Notification": Notification}


if __name__ == "__main__":
    app.run()
