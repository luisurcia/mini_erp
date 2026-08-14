import click
from flask import Flask

from app.extensions import db
from app.models.user import User


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Populate the database with kombucha demo data."""
        from app.seed import seed_demo_data

        db.create_all()
        seed_demo_data(app)
        click.echo("Demo data seeded.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, password):
        """Create (or update the password of) the admin user."""
        db.create_all()
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            db.session.add(user)
        user.set_password(password)
        db.session.commit()
        click.echo(f"Admin user '{username}' is ready.")
