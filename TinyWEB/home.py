#https://flask.palletsprojects.com/en/1.0.x/tutorial/blog/

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flask import Flask

from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

from TinyWEB.auth import login_required
from TinyWEB.database import get_db
from TinyWEB import webfileserver

from TinyWEB import db,app, folderout , deliverables_folder
from TinyWEB.models import Part, Bom , solidbom
from sqlalchemy import or_

import os

bp = Blueprint('home', __name__)



@bp.route('/', methods=('GET', 'POST','PUT'))
def index(page=1):

     if request.method == 'POST':
        search ="%"+ request.form['search']+"%"
        #print(search)
        error = None

        if not search:
            error = 'A text string required'

        if error is not None:
            flash(error)
        else:
             
            pagination =  Part.query.filter(or_(Part.description.like(search),Part.partnumber.like(search))).order_by(Part.partnumber.desc()).paginate(
                                                 page, per_page=12,
                                                   error_out=False)
            results=pagination.items
            for part in results:
                 part.updatefilespath(webfileserver)

            return render_template('part/allparts.html',title="Tiny MRP", parts=results,pagination=pagination)
   
     return render_template('home/index.html',title="Tiny MRP")






