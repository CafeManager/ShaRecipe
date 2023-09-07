from flask import Flask, request, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
from sqlalchemy.dialects.postgresql import JSON

bcrypt = Bcrypt()
db = SQLAlchemy()


def connect_db(app):
    db.app = app
    db.init_app(app)


class User(db.Model):
    """User in the system."""

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password):
        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Recipe(db.Model):
    "Recipe."

    def __repr__(self):
        p = self
        return f"<Recipe id={p.id} name={p.name}>"

    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.Time, nullable=False, default=datetime.now())

    created_by = db.Column(db.Text, nullable=False)

    total_time = db.Column(db.Integer, nullable=False)

    total_servings = db.Column(db.Integer, nullable=False)

    api_id = db.Column(db.Integer, nullable=False)

    parent_recipe_id = db.Column(db.Integer, nullable=False)



class Ingredient(db.Model):
    "Ingredient."

    def __repr__(self):
        p = self
        return f"<Ingredient id={p.id} recipe={p.json}>"

    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    json = db.Column(JSON, nullable=False)

    amount = db.Column(db.Integer, nullable=False)

    recipe_id = db.Column(db.Integer, nullable=False)


class Step(db.Model):
    "Step."

    def __repr__(self):
        p = self
        return f"<Step id={p.id} recipe={p.recipe}>"

    __tablename__ = "steps"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    json = db.Column(JSON, nullable=False)

    recipe_id = db.Column(db.Integer, nullable=False)

