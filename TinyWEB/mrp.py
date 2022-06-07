from TinyWEB.models import *
from TinyWEB import *

#SQL libraries
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.types import Integer, Float, Boolean,String,Text,NVARCHAR, Date
from flask import render_template, jsonify, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, ForeignKey,select, or_, and_
from sqlalchemy.orm import relationship, backref



#Job class definition

class Job(db.Model):
    # Defines the Table Name user
    __tablename__ = "job"
    
	# Makes three columns into the table id, name, email
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jobnumber = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    customer =db.Column(db.String)
    bompart=db.Column(db.String)
    #bompartrev==db.Column(db.String)



    def __init__(self, jobnumber="",description="",customer =""):

        self.jobnumber=jobnumber
        self.description=description
        self.customer=customer