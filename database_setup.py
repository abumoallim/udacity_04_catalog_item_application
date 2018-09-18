import os
import sys
import datetime
import random
import string
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# User Model
class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(20), unique=True, index=True)
    password = db.Column('password', db.String(10))
    email = db.Column('email', db.String(50), unique=True, index=True)
    social_auth_token = db.Column(
        'social_auth_token', db.String(50), default="")
    token = db.Column('token', db.String(50), default="")
    registered_on = db.Column(
        'registered_on', db.DateTime, default=datetime.datetime.utcnow)


    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.id)

    def __repr__(self):
        return (self.username)


# Catalog Model
class Catalog(db.Model):
    __tablename__ = "catalog"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_by = db.relationship(User)
    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
        }
    
    def is_creator(self, User):
        return self.created_by == user 


# Catalog Item
class CatalogItem(db.Model):
    __tablename__ = "catalog_item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalog.id'))
    catalog = db.relationship(Catalog)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_by = db.relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'catalog_id': self.catalog_id,
        }

    def is_creator(self, User):
        return self.created_by == user
