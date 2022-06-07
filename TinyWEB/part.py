#https://flask.palletsprojects.com/en/1.0.x/tutorial/blog/

from flask import (
    Blueprint, flash, g, redirect, session, render_template, request, url_for
)
from werkzeug.exceptions import abort

from TinyWEB.auth import login_required
from TinyWEB.database import get_db
from TinyWEB.models import Part

from TinyWEB import webfileserver,process_conf
from TinyWEB import db,app, folderout , deliverables_folder, webfileserver, fileserver_path, deliverables
from TinyWEB.models import Part, Bom , solidbom, Comment,User,create_folder_ifnotexists
from TinyWEB.report import *
from TinyWEB.publisher import IndexPDF, pdfListCompile, bom_to_excel, get_files,get_all_files, visual_list, label_list, loadexcelcompilelist

#For raw text queries on database
from sqlalchemy.sql import text
from sqlalchemy.sql import func
from sqlalchemy import or_ , and_,not_

import os
from pathlib import Path

import shutil
from shutil import copyfile
from werkzeug.utils import secure_filename


#Testing flask WTF to make forms easier
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed


from wtforms import StringField, SubmitField,SelectField,TextAreaField, RadioField
from wtforms.validators import DataRequired

from datetime import datetime, date




#Setup for blueprint and pagination
bp = Blueprint('part', __name__)
pagination_items=15




#Forms definition


class PartComment(FlaskForm):
    body = TextAreaField('Add a comment', validators=[DataRequired()])
    category=RadioField('Comment type', validators=[DataRequired()],choices=[('review','Design review'),('improvement','improvement'),('mistake','mistake'),('procurement','procurement'),('ideas','ideas')])
    pic_path = FileField('Attach file',validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')


class PartReport(FlaskForm):
    body = TextAreaField('Add a comment', validators=[DataRequired()])
    category=RadioField('Comment type',choices=[('improvement','improvement'),('mistake','mistake'),('procurement','procurement')])
    pic_path = FileField('Attach file',validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')    



#Used functions

import copy
def tree_dict (partin):
    #creates a dictionary with the tree of the part
        reflist=[]
        flatbom=[]

        partin.updatefilespath(webfileserver)
        
        partdict0=partin.as_dict()
        partdict=copy.copy(partdict0)
        partdict['children']=[]
        ##print(partdict)

        def loopchildren(partdict,qty,reflist):
            partnumber=partdict['partnumber']
            revision=partdict['revision']
            
            
            part_loop=Part.query.filter_by(partnumber=partnumber,revision=revision).first()
            
            
            
            children_loop=part_loop.children_with_qty()
            
            
            if len(children_loop)>0:
                ##print("level",part_loop.partnumber)
                partdict['children']=[]
   
            for child_loop in children_loop:
                ##print(child_loop)
                child_loop.pngpath="xxxxx"
                #print(child_loop.pngpath)
                child_loop.updatefilespath(webfileserver)
                #print('object',child_loop.pngpath)
                test=child_loop.pngpath
                #print(test)
                child_dict0=child_loop.as_dict()
                child_dict=copy.copy(child_dict0)
                child_dict['pngpath']=test
                #print('dict png path',child_dict['pngpath'])
                child_dict['branch_qty']=child_loop.qty*qty
                child_dict['qty']=child_loop.qty

                
                if  len(child_loop.children)>0:
                    
                    #try:
                        loopchildren(child_dict, child_dict['branch_qty'],reflist)
                    #except:
                     #   #print("Problem with", child_loop.partnumber)
                      #  #print(traceback.format_exc())

                reflist.append(((child_dict['partnumber'],child_dict['revision']),child_dict['branch_qty']))
                    
                partdict['children'].append(child_dict)
                    
        loopchildren(partdict,1,reflist)
        
        #Sum up all quantities and compile flatbom
        resdict={}
        for item,q in reflist:
            total=resdict.get(item,0)+q
            resdict[item]=total
        
        for partrev in resdict.keys():
            flatbom.append({'partnumber':partrev[0],'revision':partrev[1],'total_qty':resdict[partrev]})
            #part.qty=resdict[part]
            #flatbom.append(part)
        
        #flatbom.sort(key=lambda x: (x.category,x.supplier,x.oem,x.approved,x.partnumber))
        
        ##print(len(flatbom))
        ##print(flatbom)
        partdict['flatbom']=flatbom
        
        return partdict



@bp.route('/product', methods=('GET', 'POST'))
@bp.route('/product/page/<int:page>', methods=('GET', 'POST'))
def allproducts(page=1):
    if request.method == 'POST':
        search ="%"+ request.form['search']+"%"
        searchstring=request.form['search']
        #print(search)
        error = None

        if not search:
            error = 'A text string required'

        if error is not None:
            flash(error) 
        else:

            allparts=Part.query.filter(or_(Part.description.like(search),
                                           Part.partnumber.like(search))).order_by(Part.partnumber.desc())
            # allparts=Part.query.filter(or_(Part.description.like(search),
            #                                Part.partnumber.like(search))).order_by(Part.partnumber)
         

            if 'rev' in request.form:
                allparts=allparts.filter(Part.revision!="")
            if 'assy' in request.form:
                allparts=allparts.filter(or_(Part.process=="assembly"))
            pagination =  allparts.paginate( page, per_page=pagination_items,
                                             error_out=False)
            parts=pagination.items
            for part in parts:
                 part.updatefilespath(webfileserver, png_thumbnail=True)
            session['search']=searchstring
            return redirect(url_for('part.productsearch',searchstring=searchstring,page=1 ))
            #return render_template('part/search.html', parts=parts,searchstring=searchstring,pagination=pagination,page=1)
           
    page = request.args.get('page', page, type=int)
    #print(page)
    
    
    #allparts=Part.query.filter(Part.asset!="").filter(Part.asset!="FALSE").filter(Part.asset!="False").filter(Part.process!="hardware").order_by(Part.id.desc())
    
    allparts=Part.query.filter(Part.asset!="").filter(Part.asset!="FALSE").filter(Part.asset!="False").filter(Part.process!="hardware").order_by(Part.partnumber)
    
    allparts=allparts.filter(not_(Part.partnumber.like("opy of")))
    allparts=allparts.filter(or_(Part.partnumber.like("AWS%"),Part.partnumber.like("OEM%")))
    pagination = allparts.paginate(
        page, pagination_items,
        error_out=False)
    parts = pagination.items



    for part in parts:
        part.updatefilespath(webfileserver)
        #print (part.pdf)
   
    ##print(app.config['PROCESS_LEGEND'])

    return render_template('part/allproducts.html',title="Product list", parts=parts,pagination=pagination,page=1, legend=app.config['PROCESS_LEGEND'])



@bp.route('/part', methods=('GET', 'POST'))
@bp.route('/part/page/<int:page>', methods=('GET', 'POST'))
def allparts(page=1, assets=False):
    if request.method == 'POST':
        search ="%"+ request.form['search']+"%"
        searchstring=request.form['search']
        #print(search)
        error = None

        if not search:
            error = 'A text string required'

        if error is not None:
            flash(error) 
        else:

            allparts=Part.query.filter(or_(Part.description.like(search),
                                           Part.partnumber.like(search))).order_by(Part.partnumber.desc())
            # allparts=Part.query.filter(or_(Part.description.like(search),
            #                                Part.partnumber.like(search))).order_by(Part.partnumber)
         

            if 'rev' in request.form:
                allparts=allparts.filter(Part.revision!="")
            if 'assy' in request.form:
                allparts=allparts.filter(or_(Part.process=="assembly"))
            pagination =  allparts.paginate( page, per_page=pagination_items,
                                             error_out=False)
            parts=pagination.items
            for part in parts:
                try:
                    part.updatefilespath(webfileserver, png_thumbnail=True)
                except:
                    flash('Filelinks not updated for', part)
            session['search']=searchstring
            return redirect(url_for('part.search',searchstring=searchstring,page=1 ))
            #return render_template('part/search.html', parts=parts,searchstring=searchstring,pagination=pagination,page=1)
           
    page = request.args.get('page', page, type=int)
    #print(page)
    
    
    #allparts=Part.query.filter(Part.asset!="").filter(Part.asset!="FALSE").filter(Part.asset!="False").filter(Part.process!="hardware").order_by(Part.id.desc())

    allparts=Part.query.filter(Part.process!="hardware").order_by(Part.partnumber)
    allparts=allparts.filter(not_(Part.partnumber.like("opy of")))
    allparts=allparts.filter(or_(Part.partnumber.like("AWS%"),Part.partnumber.like("OEM%")))
    pagination = allparts.paginate(
        page, pagination_items,
        error_out=False)
    parts = pagination.items



    for part in parts:
        part.updatefilespath(webfileserver)
        #print (part.pdf)
   
    ##print(app.config['PROCESS_LEGEND'])

    return render_template('part/allparts.html',title="Part list", parts=parts,pagination=pagination,page=1, legend=app.config['PROCESS_LEGEND'])




@bp.route('/part/search', methods=('GET', 'POST'))
@bp.route('/part/search/<searchstring>/<int:page>', methods=('GET', 'POST'))
def search(searchstring="aws",page=1):
    if 'search' in session.keys():
        search="%"+ searchstring+"%"
        search="%"+ session['search']+"%"
    else:
        search=""

    #print(session['search'])

    if request.method == 'POST':
        searchstring=request.form['search']
        session['search']=searchstring
        search ="%"+ searchstring+"%"

    

        
        return redirect(url_for('part.search',searchstring=searchstring,page=1 ))
        
    
    allparts=Part.query.filter(or_(Part.description.like(search),
                               Part.partnumber.like(search))).order_by(Part.id.desc())
    #allparts=allparts.filter(not_(Part.partnumber.like("opy of"))).filter(Part.revision!="")
           
    
    if request.method == 'GET' :
        
        #print("GET in search.py")
        #print(searchstring)
        pagination = allparts.paginate(
            page, pagination_items,
            error_out=False)
        parts = pagination.items

        #parts=Part.query.all()

        for part in parts:
            part.updatefilespath(webfileserver)
            #print (part.pdf)
   
    
        return render_template('part/search.html', parts=parts,searchstring=session['search'],pagination=pagination,page=page,legend=app.config['PROCESS_LEGEND'])






@bp.route('/product/search', methods=('GET', 'POST'))
@bp.route('/product/search/<searchstring>/<int:page>', methods=('GET', 'POST'))
def productsearch(searchstring="aws",page=1):
    search="%"+ searchstring+"%"
    search="%"+ session['search']+"%"
    #print(session['search'])

    if request.method == 'POST':
        searchstring=request.form['search']
        session['search']=searchstring
        search ="%"+ searchstring+"%"
        
        return redirect(url_for('part.productsearch',searchstring=searchstring,page=1 ))
        
    
    allparts=Part.query.filter(Part.asset!="").filter(Part.asset!="FALSE").filter(Part.asset!="False").filter(Part.process!="hardware").order_by(Part.partnumber)
    
    allparts=allparts.filter(not_(Part.partnumber.like("opy of")))
    allparts=allparts.filter(or_(Part.partnumber.like("AWS%"),Part.partnumber.like("OEM%")))
    #allparts=allparts.filter(not_(Part.partnumber.like("opy of"))).filter(Part.revision!="")
           
    
    if request.method == 'GET' :
        
        #print("GET in search.py")
        #print(searchstring)
        pagination = allparts.paginate(
            page, pagination_items,
            error_out=False)
        parts = pagination.items

        #parts=Part.query.all()

        for part in parts:
            part.updatefilespath(webfileserver)
            #print (part.pdf)
   
    
        return render_template('part/search.html', parts=parts,searchstring=session['search'],pagination=pagination,page=page,legend=app.config['PROCESS_LEGEND'])





@bp.route('/part/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        partnumber = request.form['partnumber']
        revision = request.form['revision']
        description = request.form['description']
        error = None

        if not partnumber:
            error = 'Pasrtnumber is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO part (partnumber,revision, description)'
                ' VALUES (?, ?, ?)',
                (partnumber,revision, description)
            )
            db.commit()
            return redirect(url_for('part.index'))

    return render_template('part/create.html')

#Keeping previous link specially for links from outside
@bp.route('/part/<partnumber>_rev_<revision>', methods=('GET', 'POST'))
def details(partnumber,revision=""):
    return redirect( url_for('part.partnumber',partnumber=partnumber,revision=revision,detail="quick") )



#Detail valid inputs: "quick" and "full"
@bp.route('/part/detail/<detail>:<partnumber>_rev_<revision>', methods=('GET', 'POST'))
#@bp.route('/part/<partnumber>_rev_<revision>/page/<int:page>', methods=('GET', 'POST'))
def partnumber(partnumber,revision="",detail="full",page=1):
    commentform=PartComment()

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        ##print(partnumber)
        #print("-",revision)
        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()
        if part==None:
            part=Part.query.filter_by(partnumber=partnumber).order_by(Part.revision.desc()).first()
        parts=part.children_with_qty()

        hardware=[]
        composed=[]
        composedicons=[]
        composedprocesses=[]

        #UPdate related part files location to the webserver
        part.updatefilespath(webfileserver)



        legend=app.config['PROCESS_LEGEND']
        needed_processes=[]
        icons=[]
        colors=[]

        #Include top part processes in the required processes
        for process in process_conf.keys():
            #To only show the used processes uncomment line below        
            if part.hasProcess(process) and  process not in needed_processes :
                        needed_processes.append(process)
        
        #Detailed part bom info check
        if detail=="full":
            #Toget the full flat bom
            flatbom=part.get_components()

            #print("original flatbom length", len(flatbom))
            #To limit the amount of parts displayed - no need anymore with the full details new page
            #if len(flatbom)>350 :
            #    flatbom=[x for x in flatbom if len(x.children)>0 ]
            #    #flatbom=[x for x in flatbom if x.hasProcess("assembly") or x.hasProcess("welding") or x.hasProcess("paint") ]
            #print("after reduction for too many parts", len(flatbom))


      
            for parto in flatbom:
                parto.updatefilespath(webfileserver,png_thumbnail=True)
                parto.MainProcess()
                for process in process_conf.keys():
                        if parto.hasProcess(process) and  process not in needed_processes :
                            needed_processes.append(process)
                if (not parto.process in process_conf.keys() or \
                   (parto.process2!="" and not parto.process2 in process_conf.keys() )or \
                   (parto.process3!="" and not parto.process3 in process_conf.keys() )) and \
                   "others" not in needed_processes:
                        needed_processes.append( "others")
                if  (bool(parto.process) ^ bool(parto.process2)  ^ bool(parto.process3)):
                    #print (parto.partnumber)
                    pass
                else:
                    print (parto.partnumber, parto.process,parto.process2,parto.process3)
                    composed_process=[parto.process,parto.process2,parto.process3]
                    composed_process.sort()
                    composed_process=set([x for x in composed_process if x!=""])
                    composed.append(parto)
                    parto.composed_process=composed_process
                    if len(composed_process)>1 and not composed_process in composedprocesses:
                        composedprocesses.append(composed_process)
                        comp_icon=[process_conf[process]['icon'] for process in composed_process]
                        composedicons.append(comp_icon)
                

            # #PRint the composed process for checking
            # for comp in composedprocesses:
            #         #print(comp)

            #  #PRint the composed process for checking
            # for icon in composedicons:
            #         #print("icon ",icon)
        else:
            flatbom=""
        
        #To get the top level flatbom and having better resolution from them
        # due to the updatefilespath function affection all the parts (database object)
        for parto in parts:
            if parto.process=="hardware":
                hardware.append(parto)
            else:

                parto.updatefilespath(webfileserver)

                for process in process_conf.keys():
                    if parto.hasProcess(process) and  process not in needed_processes :
                        needed_processes.append(process)
        #print(needed_processes)



        for parto in hardware:
            parts.remove(parto)

        parents=part.parents_with_qty()

        for parto in parents:
            parto.updatefilespath(webfileserver)

        comments=[]
        for comment in part.comments:
            comment.username=User.query.filter_by(id=comment.user_id).first().username
            comments.append(comment)

        



        for process in needed_processes:
            try:
                icons.append(process_conf[process]['icon'])
                colors.append(process_conf[process]['color'])
            except:
                pass
                #print("No icon for ", process)

        legend=[ {'process':process,'icon':'images/'+icon,'color':color} for  (process,icon,color) in zip(needed_processes,icons,colors) ]

        #print("THIS IS THE ", legend)


        return render_template("part/details.html",part=part,parts=parts,
                               hardware=hardware,parents=parents,
                               commentform=commentform,
                               comments=comments,flatbom=flatbom
                               , legend=legend, title=part.partnumber, processes=needed_processes, 
                               composed=composed,composedprocesses=composedprocesses)
    else:
        error = 'Cannot get part detials ' + partnumber + " rev " + revision
        flash(error)

    if request.method == 'POST':
        if 'search' in request.form:
            if  request.form[ 'search']!="":
            
                search ="%"+ request.form['search']+"%"
                session['search']=search
        
                error = None

                if not search:
                    error = 'A text string required'

                if error is not None:
                    flash(error)
                else:

                    return redirect(url_for('part.search',searchstring=search,page=1 ))
        else:
            part=Part.query.filter_by(partnumber=partnumber,revision=rev).first()


            if   (commentform.pic_path.data):
                f = commentform.pic_path.data
                filename = part.partnumber+"_REV_"+part.revision+ "-comment-" + datetime.now().strftime('%d_%m_%Y-%H_%M_%S')+ "-"  +  secure_filename(f.filename)
                localfilename =os.path.join(app.config['PIC_LOCATION'], filename)
                f.save(localfilename)
                flash('Pic uploaded successfully.')

                comment=Comment(part_id=part.id,
                            user_id=g.user['id'],
                            created=func.now(),
                            body=commentform.body.data,
                            category=commentform.category.data, 
                            pic_path=webfileserver+"/Deliverables/pic/"+filename                            
                            )
            else:
                filename =""
                comment=Comment(part_id=part.id,
                            user_id=g.user['id'],
                            created=func.now(),
                            body=commentform.body.data,
                            category=commentform.category.data, 
                            pic_path=""                            
                            )
            


            refpart=part.partnumber
            refrev=part.revision
            if refrev=="": refrev="%"
            db.session.add(comment)
            db.session.commit() 
            db.session.close()
            
            return redirect(url_for('part.details',partnumber=refpart,revision=refrev ))
            

    
@app.route('/part/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # try:
            f = request.files['file']
            folder= os.path.dirname(os.path.abspath(__file__))
            targetfile= folder+ "/" + app.config['UPLOAD_PATH']+ "/" + secure_filename(f.filename)
            f.save(targetfile)        
            #print(folderout)
            bom_in=solidbom(targetfile,deliverables_folder,fileserver_path+folderout)
            try:
                os.remove(targetfile)
            except:
                #print("Couldn't erase upload file ", targetfile)
                flash("Couldn't erase upload file ", targetfile)

            flash("BOM uploaded successfully")

            if bom_in.revision=="":
                bom_in.revision="%25"
            
            return redirect(url_for('part.details',partnumber=bom_in.partnumber,revision=bom_in.revision ))            
           
        # except:
        #     # searchstring=request.form['search']
        #     # session['search']=searchstring
        #     # search ="%"+ searchstring+"%"
        #     # return redirect(url_for('part.search',searchstring=searchstring,page=1 ))
        #     return render_template('upload.html',upload=False)
    else:
        return render_template('upload.html',upload=False)



@app.route('/part/excelcompile', methods = ['GET', 'POST'])
def excelcompile():
    if request.method == 'POST':

            f = request.files['file']
            folder= os.path.dirname(os.path.abspath(__file__))
            
            targetfile= folder+ "/" + app.config['UPLOAD_PATH']+ "/" + secure_filename(f.filename)
            
            try:
                os.remove(targetfile)
            except:
                pass
            
            f.save(targetfile)        
            #print(folderout)
            flatbom,listofobjects=loadexcelcompilelist(targetfile,export_objects=True)
            #print(flatbom)

            try:
                include_children=request.form.getlist('include_children')[0]
            except:
                include_children=""
            # children=[]
            # if include_children=='include':
            #     for item in listofobjects:
            #         for child in item.children_with_qty():
            #             children.append(child)
            #     listofobjects=listofobjects+children
            

                
            
    

            flash("Excel file uploaded successfully")
            #print(flatbom)
            # print(listofobjects)

            if include_children=='include':
                return(purchasepack("","",excelflatbom=flatbom,listofobjects=listofobjects))
            else:                
                #Create export folder and alter the output folder and create it
                summaryfolder=os.getcwd()+"/temp/"+"excelcompile"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
                create_folder_ifnotexists(summaryfolder)

                
                
                bomartificial=solidbom.solidbom_from_flatbom(listofobjects,listofobjects[0],outputfolder=summaryfolder,sort=False)
                pdf_pack=IndexPDF(bomartificial,outputfolder=summaryfolder,savevisual=True,sort=False,norefpart=True)
                
                #Copy original excel file to export folder
                shutil.copy2(Path(targetfile),Path(summaryfolder+"inputfile"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+".xlsx") )


                #Get all files of the flatbom
                get_all_files(flatbom,summaryfolder)

                
                

                #Compile all in a zip file
                zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
                #print("original " ,zipfile)

                path, filename = os.path.split(zipfile)
                finalfile=fileserver_path+deliverables_folder+"temp/"+filename
                #print("final " ,finalfile)


                shutil.copy2(Path(zipfile),Path(finalfile) )
                
                #Remove all the temp files
                os.remove(zipfile)
                shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

                #Create the web link 
                weblink="http://"+finalfile.replace(fileserver_path,webfileserver)


                #Clean original file
                try:
                    
                    os.remove(targetfile)
                except:
                    #print("Couldn't erase upload file ", targetfile)
                    flash("Couldn't erase upload file ", targetfile)
                
                return redirect(weblink)   
           
    else:
        return render_template('excelcompile.html',upload=False)

    
@bp.route('/part/dpack/<partnumber>_rev_<revision>/drawingpack?components_only=<components_only>', methods=('GET', 'POST'))
def drawingpack(partnumber,revision,components_only="NO"):
    
    components_only=request.args.get('components_only',default = '*', type = str)


    if components_only=="YES":
        components_only=True
    elif components_only=="NO":
        components_only=False
    else:
        components_only=False



    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #Set qty to one to compute the rest
    part.qty=1

    flatbom=[]
    flatbom.append(part)
    flatbom=flatbom+part.get_components(components_only=components_only)
    #print(flatbom)

    

    bom_solidbomobject=solidbom.solidbom_from_flatbom(flatbom,part)
    #print(bom_solidbomobject.tag)


    summaryfolder=os.getcwd()+"/temp/"+bom_solidbomobject.tag+"/"
    bomtitle="-manufacturing list-"
    create_folder_ifnotexists(summaryfolder)



    #print(bom_solidbomobject.folderout)
    pdf_pack=IndexPDF(bom_solidbomobject,outputfolder=summaryfolder,sort=False)
    #print(pdf_pack)

    path, filename = os.path.split(pdf_pack)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename


    shutil.move(pdf_pack,finalfile )

    finalfile=finalfile.replace(fileserver_path,webfileserver)
    #print(finalfile)
    #print("changes?")
    

    return redirect("http://"+finalfile)

@bp.route('/part/<partnumber>_rev_<revision>/fabrication', methods=('GET', 'POST'))
def fabrication(partnumber,revision):
    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
    flatbom=flatbom+part_in.get_components()

    #Extract the welding components
    if part_in.hasProcess("welding"):
        manbom=[]
        manbom.append(part_in)
    else:
        manbom= [x for x in flatbom if x.hasProcess("welding") ]

    if len(manbom)==0 and part_in.hasProcess("welding"):
        manbom.append(part_in)
    elif len(manbom)==0:
        return "NO FABRICATION AVAILABLE IN THE PARTNUMBER"
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-fabrication_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder

    #Create list with title
    bomtitle=bom_in.tag+"- scope of supply"
    excel_list=bom_to_excel(bom_in.flatbom,bom_in.folderout,title=bomtitle,qty="qty", firstrow=1)

    #Copy root part image and drawing
    path, filename = os.path.split(part_in.pngpath)
    copyfile(part_in.pngpath,summaryfolder+filename)

    

    #Machined parts used in fabrication
    machined=[]

    drawingpacklist=[]

    #Loop over the fabrication components and create files
    for index,component in enumerate(manbom):
        
        #Get flatbom for each component
        com_flatbom=[]
        com_flatbom.append(component)
        com_flatbom=com_flatbom+component.get_components(components_only=False)

        #Get the machined components:
        #for mach_comp in com_flatbom:
        #    if mach_comp.hasProcess("machine"):
        #        machined.append(mach_comp)

                
        #Create the flatbom for each man item and alter the output folder and create it
        com_bom=solidbom.solidbom_from_flatbom(com_flatbom,component)
        com_bom.folderout=summaryfolder+com_bom.partnumber+"/"
        create_folder_ifnotexists(com_bom.folderout)

        #Create the drawing pack (pdf)
        com_dwgpack=IndexPDF(com_bom,outputfolder=com_bom.folderout,sort=False)

        #Get manufacturing files
        get_files(com_bom.flatbom,'dxf',com_bom.folderout)
        get_files(com_bom.flatbom,'step',com_bom.folderout)
        get_files(com_bom.flatbom,'pdf',com_bom.folderout)
        get_files(com_bom.flatbom,'png',com_bom.folderout)
        get_files(com_bom.flatbom,'3D-edrawing',com_bom.folderout)

        #Create the bom title
        bomtitle=com_bom.tag+"-components list"

        #Crete excelist
        excel_list=bom_to_excel(com_bom.flatbom,com_bom.folderout,title=bomtitle,qty="qty")

        #print(com_bom.folderout)
        com_dwgpack=IndexPDF(com_bom,outputfolder=com_bom.folderout,sort=False)
        #print(com_dwgpack)

        drawingpacklist.append(com_dwgpack)

    #create a top level drawing pack to combine with all
    topflatbom=solidbom.solidbom_from_flatbom(manbom,part_in)
    title=topflatbom.partnumber+ "_rev_"  + topflatbom.revision+ \
                "-SCOPE OF SUPPLY ITEMS DRAWINGS-" + topflatbom.timestamp 

    toplevelpack=IndexPDF(topflatbom,outputfolder=summaryfolder,sort=False, title=title)
    drawingpacklist.insert(0,toplevelpack)
    
    #Combine all the drawing packs into one file:
    title=topflatbom.partnumber+ "_rev_"  + topflatbom.revision+ \
                "-ALL DRAWINGS INCLUDING SUBCOMPONENTS IN ONE FILE-" + topflatbom.timestamp 
    pdfListCompile(drawingpacklist,summaryfolder+title+".pdf")

        


    zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
    #print("original " ,zipfile)

    path, filename = os.path.split(zipfile)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    #print("final " ,finalfile)


    shutil.copy2(Path(zipfile),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)


@bp.route('/part/<partnumber>_rev_<revision>/<processin>_componentsonly_<components_only>', methods=('GET', 'POST'))
def process_docpack(partnumber,revision,processin,components_only):

    #Remove spaces from link
    process=processin.replace('%20',' ')

    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)
    

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
      
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
        

    #Extract the process related components components
    part_in.MainProcess()
    #if part_in.hasProcess(process):



    #print("fodsfgsdfgsdgsdfgsdfgsdfgsdfgdsfgsdfgsdfgfdsgo")
    if process=='assembly' and components_only=="YES":
        manbom= [x for x in flatbom ]

    elif components_only=="YES":

        manbom= [x for x in flatbom if x.MainProcess()==process ]
    else:
        manbom=[x for x in flatbom if x.isMainProcess(process) ]

    
    
    if len(manbom)==0 and part_in.isMainProcess(process):
        manbom.append(part_in)
    elif part_in.isMainProcess(process) and (not (part_in in manbom)):
        manbom.append(part_in)
    elif len(manbom)==0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper()+"-components_only_"+components_only +"_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder



    #Add full doc compile
    pdf_pack=IndexPDF(bom_in,outputfolder=summaryfolder,savevisual=True,sort=False,norefpart=True)
 

    #Create list with title
    bomtitle=bom_in.tag+"- scope of supply"
    #excel_list=bom_to_excel(bom_in.flatbom,bom_in.folderout,title=bomtitle,qty="qty", firstrow=1)
    #excel_list=bom_in.solidbom_to_excel(process=processin)
    excel_list=bom_to_excel(bom_in.flatbom,bom_in.folderout,title=process+"-"+ bomtitle,qty="qty", firstrow=1)

    #Copy root part image and drawing
    path, filename = os.path.split(part_in.pngpath)
    copyfile(part_in.pngpath,summaryfolder+filename)


    #Get manufacturing files
    if process=="machine"  or  process=="folding"  or process=="profile cut"  or process=="3d laser"   or process=="3d print"  or process=="rolling" :
        get_files(bom_in.flatbom,'step',summaryfolder)
    
    if process!="hardware":
        get_files(bom_in.flatbom,'png',summaryfolder)

    if process=="lasercut" or  process=="folding"  or  process=="machine" or process=="profile cut"   :
        get_files(bom_in.flatbom,'dxf',summaryfolder)

    get_files(bom_in.flatbom,'pdf',summaryfolder)

    #Compile all in a zip file
    zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
    #print("original " ,zipfile)

    path, filename = os.path.split(zipfile)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    #print("final " ,finalfile)


    shutil.copy2(Path(zipfile),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)



@bp.route('/part/<partnumber>_rev_<revision>/<processin>_<components_only>', methods=('GET', 'POST'))
def process_visuallist(partnumber,revision,processin,components_only):

    #Remove spaces from link
    process=processin.replace('%20',' ')


    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
       
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True,process=process)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False,process=process)
    
    



    #Extract the process related components components
    part_in.MainProcess()

    # if part_in.hasProcess(process):
    #     manbom=[]
    #     manbom.append(part_in)


    if process=="toplevel":
        manbom= [x for x in part_in.children if not x.hasProcess("hardware") ]
    elif process=="all":
        manbom= [x for x in flatbom if not x.hasProcess("hardware") ]
    elif process=='receiving':
        manbom=[x for x in flatbom]
    elif process=='assembly'  and components_only=="YES":
        manbom= [x for x in flatbom if not x.hasProcess("hardware")]
    
    elif components_only=="YES":
        manbom= [x for x in flatbom if x.MainProcess()==process ]
    else:
        manbom= [x for x in flatbom if x.isMainProcess(process) ]



    if len(manbom)==0 and part_in.isMainProcess(process):
        manbom.append(part_in)
    elif part_in.isMainProcess(process) and (not (part_in in manbom)):
        manbom.append(part_in)
    elif len(manbom)==0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())


    #Remove assembly parts only for receiving 
    noassy=[]
    noassyhardware=[]

    if  process=='receiving':
        for part in manbom:
            if (part.process + part.process2 + part.process3)!='assembly':
                if part.hasProcess('hardware'):
                    noassyhardware.append(part)
                else:
                    noassy.append(part)
        manbom=noassy

    # if process=="receiving":
    #     for part in parts:

    #         if part.process is paint or welding or purchased or machined
    #             remove children

    #         if part.process has assembly only: ignoer
   
    #Sort the list by process
    manbom=sorted(manbom, key=lambda x: x.partnumber, reverse=False)
    manbom=sorted(manbom, key=lambda x: x.process, reverse=False)

    if  process=='receiving':
        manbom=manbom+noassyhardware
        
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() +"_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder




    #Assign title
    if process=="toplevel":
        visualtitle="Top level components"
    else:
        visualtitle="Visual_list-"+process.upper()

    #Create the visual list
    visuallist=visual_list(bom_in, outputfolder=summaryfolder,title=visualtitle.replace(" ","_" ))

    #MOVE FILE to temp folder
    path, filename = os.path.split(visuallist)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    


    shutil.copy2(Path(visuallist),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(visuallist)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

    #print(weblink)
    
    return redirect(weblink)



@bp.route('/part/<partnumber>_rev_<revision>/flatbom_componentsonly_<components_only>', methods=('GET', 'POST'))
def flatbom(partnumber,revision,components_only):
    

    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
    
    
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
        

    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-bom/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(flatbom,part_in)
    bom_in.folderout=summaryfolder

    #Create the bom
    excelbom=bom_in.solidbom_to_excel()


    path, filename = os.path.split(excelbom)
    if components_only=="YES":
        finalfile=fileserver_path+deliverables_folder+"temp/COMPONENTS_ONLY-"+filename
        ##print("final " ,finalfile)
    else:
        finalfile=fileserver_path+deliverables_folder+"temp/FULL_FLAT_BOM-"+filename
        ##print("final " ,finalfile)


    shutil.copy2(Path(excelbom),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(excelbom)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)



@bp.route('/part/<partnumber>_rev_<revision>/treeview', methods=('GET', 'POST'))
def treeview(partnumber,revision):

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()

        treedict=tree_dict(part)
        return render_template("part/treeview.html",treedict=treedict)





@bp.route('/part/label/<partnumber>_rev_<revision>/<processin>_<components_only>', methods=('GET', 'POST'))
def process_label_list(partnumber,revision,processin,components_only):

    #Remove spaces from link
    process=processin.replace('%20',' ')


    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
       
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
    
    



    #Extract the process related components components
    if part_in.hasProcess(process):
        manbom=[]
        manbom.append(part_in)
    elif process=="toplevel":
        manbom= [x for x in part_in.children if not x.hasProcess("hardware") ]
    elif process=="all":
        manbom= [x for x in flatbom if not x.hasProcess("hardware") ]
        #Sort the list by process
        manbom=sorted(manbom, key=lambda x: x.partnumber, reverse=False)
        manbom=sorted(manbom, key=lambda x: x.process, reverse=False)
    else:
        manbom= [x for x in flatbom if x.hasProcess(process) ]



    if len(manbom)==0 and part_in.hasProcess(process):
        manbom.append(part_in)
    elif len(manbom)==0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() +"_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder

    #Assign title
    if process=="toplevel":
        visualtitle="Top level components"
    else:
        visualtitle="Visual_summary_components_only-"+components_only +"-"+process

    #Create the visual list
    visuallist=label_list(bom_in, outputfolder=summaryfolder,title=visualtitle.replace(" ","_" ))

    #MOVE FILE to temp folder
    path, filename = os.path.split(visuallist)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    


    shutil.copy2(Path(visuallist),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(visuallist)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

    #print(weblink)
    
    return redirect(weblink)






    

#Detail valid inputs: "quick" and "full"
@bp.route('/part/pdf/<partnumber>_rev_<revision>', methods=('GET', 'POST'))

def pdfwithdescription(partnumber,revision=""):
    commentform=PartComment()

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        ##print(partnumber)
        #print("-",revision)
        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()
        if part==None:
            part=Part.query.filter_by(partnumber=partnumber).order_by(Part.revision.desc()).first()


        part.updatefilespath(webfileserver)
        #MOVE FILE to temp folder
        # flash(part.pdfpath)
        path, filename = os.path.split(part.pdfpath)
        # flash(filename)
        #remove extension
        filename=os.path.splitext(filename)[0]
        # flash(filename)

        finalfile=fileserver_path+deliverables_folder+"temp/"+filename+"_"+part.description+".pdf"
        finalfile=finalfile.replace(" ","_")
        # flash(finalfile)
        
        shutil.copy2(Path(part.pdfpath.replace(webfileserver,fileserver_path)),Path(finalfile) )
        
        #Create the web link 
        weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

        ##print(weblink)
        # flash(weblink)
    
        return redirect(weblink)            
        
    if request.method == 'POST':
        if 'search' in request.form:
            if  request.form[ 'search']!="":
            
                search ="%"+ request.form['search']+"%"
                session['search']=search
        
                error = None

                if not search:
                    error = 'A text string required'

                if error is not None:
                    flash(error)
                else:

                    return redirect(url_for('part.search',searchstring=search,page=1 ))

@bp.route('/part/dxf/<partnumber>_rev_<revision>', methods=('GET', 'POST'))

def dxfwithdescription(partnumber,revision=""):
    commentform=PartComment()

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        ##print(partnumber)
        #print("-",revision)
        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()
        if part==None:
            part=Part.query.filter_by(partnumber=partnumber).order_by(Part.revision.desc()).first()


        part.updatefilespath(webfileserver)
        #MOVE FILE to temp folder
        # flash(part.pdfpath)
        path, filename = os.path.split(part.dxfpath)
        # flash(filename)
        #remove extension
        filename=os.path.splitext(filename)[0]
        # flash(filename)

        "."

        finalfile=fileserver_path+deliverables_folder+"temp/"+filename+"-"+part.material+"_"+str(part.thickness)+"mm."+"_"+part.description+".dxf"
        finalfile=finalfile.replace(" ","_")
        # flash(finalfile)
        
        shutil.copy2(Path(part.dxfpath.replace(webfileserver,fileserver_path)),Path(finalfile) )
        
        #Create the web link 
        weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

        ##print(weblink)
        # flash(weblink)
    
        return redirect(weblink)            
        
    if request.method == 'POST':
        if 'search' in request.form:
            if  request.form[ 'search']!="":
            
                search ="%"+ request.form['search']+"%"
                session['search']=search
        
                error = None

                if not search:
                    error = 'A text string required'

                if error is not None:
                    flash(error)
                else:

                    return redirect(url_for('part.search',searchstring=search,page=1 ))

            

@bp.route('/part/<partnumber>_rev_<revision>/assydocpack', methods=('GET', 'POST'))
def assydocpack(partnumber,revision):

    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)
    

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
     
     
    #Extract the process related components components
    part_in.MainProcess() 
    
    #Check if needed to consume the welded components or not 
    flatbom=flatbom+part_in.get_components(components_only=True)
        


   
    #if part_in.hasProcess(process):
    manbom= [x for x in flatbom ]


    
    
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    

    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+bom_in.tag+"/"
    bom_in.folderout=summaryfolder
    create_folder_ifnotexists(summaryfolder)

    #Add full doc compile
    pdf_pack=IndexPDF(bom_in,outputfolder=summaryfolder,savevisual=True,sort=False,norefpart=False)
 

    #Copy root part image and drawing
    path, filename = os.path.split(pdf_pack)


    finalfile=fileserver_path+deliverables_folder+"temp/"+filename


    shutil.copy(pdf_pack,finalfile )

    finalfile=finalfile.replace(fileserver_path,webfileserver)
    #print(finalfile)
    #print("changes?")
    

    return redirect("http://"+finalfile)


@bp.route('/part/<partnumber>_rev_<revision>/purchasepack', methods=('GET', 'POST'))
def purchasepack(partnumber,revision,excelflatbom=None,listofobjects=[],listofobjectsqty=[]):


   

    if listofobjects==[]:
        if revision==None or "%" in revision  or revision =="":
            rev=""
        else:
            rev=revision

        #Get the top part level object
        part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
        
        #Set qty to one to compute the rest and updatepaths
        part_in.qty=1
        part_in.updatefilespath(fileserver_path,local=True)
        
        #Add the top part to the list
        flatbom=[]
        flatbom.append(part_in)
        
        #Extract the process related components components
        part_in.MainProcess() 

        #Set qty to one to compute the rest and updatepaths
        part_in.qty=1
        part_in.updatefilespath(fileserver_path,local=True)

        #Check if needed to consume the welded components or not 
        flatbom=flatbom+part_in.get_components(components_only=True)
        flatbom_dict=[]
        for part in flatbom:
            flatbom_dict.append(copy.deepcopy(part.as_dict()))



        
        
        #Create the SolidBom class object for easier referencing, and override the output folder
        bom_in=solidbom.solidbom_from_flatbom(flatbom,part_in)
        
        #Folders and tags
        summaryfolder=os.getcwd()+"/temp/"+bom_in.tag+"/"
        visualtitle="Visual_summary-"+part_in.partnumber
    else:
        #Folders and tags
        visualtitle="Visual_summary"
        summaryfolder=os.getcwd()+"/temp/"+"excelcompile"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
        #Create fake assembly
        part_in=Part(partnumber="", revision="")
        bom_in=solidbom.solidbom_from_flatbom(listofobjects,part_in,outputfolder=summaryfolder,sort=False)
        # bom_in=solidbom.solidbom_from_flatbom(listofobjects,listofobjects[0],outputfolder=summaryfolder,sort=False)
        bom_in.tag="Excel Compile on " + datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')
        # flatbom=bom_in.flatbom
        
        
        flatbom=[]
        flatbom_dict=[]
        reflist=[]
        for x in listofobjects:
            reflist.append([x,x.qty])
      
        
        for item in listofobjects:                
                if not item.hasConsumingProcess():
                    complist=item.get_components()
                    for component in complist:
                            reflist.append([component,component.qty])

       
        resdict={}
        for item,q in reflist:
            total=resdict.get(item,0)+q
            resdict[item]=total
            print(item,total)


        for part in resdict.keys():
            part.qty=resdict[part]
            part.totalqty=resdict[part]
            flatbom.append(part)
            flatbom_dict.append(copy.deepcopy(part.as_dict()))
  
        # for item in flatbom:            
        #     print("Flatbom before procurement",item.totalqty,item.qty,item.partnumber)

        #input("whateve")
         
      


    #Create export folder and alter the output folder and create it
    
    bom_in.folderout=summaryfolder
    create_folder_ifnotexists(summaryfolder)



    #Consumed components blank list
    consumedlist=[]
    

    for item in flatbom_dict:
        part=Part.partFromDict(item)

        
        # parent=str(i)
        if part.hasConsumingProcess():
            complist, pro_consumed_list=part.get_components(list_consumed=True,consumedtodict=True)            
            for component in pro_consumed_list:
                        # tempdict=component.as_dict()                       
                        consumedlist.append(component)


        # for i,part in enumerate(flatbom):                    
        # if part.hasConsumingProcess():
        #     complist, pro_consumed_list=part.get_components(list_consumed=True)
        #     for component in pro_consumed_list:
        #             consumedlist.append(component.as_dict(parent=str(i)+"-"+part.tag))

    cleanconsumelist=[]


    for part in consumedlist:
        print(part['qty'],part['partnumber'],part['parent'])
        addtolist=True
        for partcon in cleanconsumelist:            
            if partcon['partnumber']==part['partnumber'] and partcon['revision']==part['revision'] :
                addtolist=False
                if not part['parent'] in partcon['parent']:
                    partcon['qty']=partcon['qty']+part['qty']

                    if type(partcon['parent'])==list:
                        partcon['parent'].append(part['parent'])
                    else:
                        partcon['parent']=[partcon['parent']]
                        partcon['parent'].append(part['parent'])
              
        if addtolist:
            cleanconsumelist.append(part)
    
    for part in cleanconsumelist:
        if not type(part['parent'])==list:
            part['parent']=[part['parent']]

    print("cleanconsumelistcleanconsumelistcleanconsumelistcleanconsumelistcleanconsumelistcleanconsumelist")
    for x in cleanconsumelist:
        print(x['partnumber'])
    print("cleanconsumelistcleanconsumelistcleanconsumelistcleanconsumelistcleanconsumelistcleanconsumelist")



    #################################
    #Process loops
    ##############################
    #print(process_conf)

    dupcheck=[]

    for process in process_conf.keys():

        processdict=process_conf[process]

        #lists
        processlist=[]
        processfiles=[]
        
        #Files required
        #print(process)
        #print(processdict['dxf'])
        if str(processdict['dxf']).lower()=="yes": processfiles.append('dxf')
        if str(processdict['pdf']).lower()=="yes": processfiles.append('pdf')
        if str(processdict['step']).lower()=="yes": processfiles.append('step')
                   
               
        for partdict in flatbom_dict: 
            part=Part.partFromDict(partdict)                   
            if part.hasProcess(process):
                if not((part.partnumber+part.revision)  in dupcheck):
                    processlist.append(partdict)
                    dupcheck.append(part.partnumber+part.revision)


                    # if not part.hasConsumingProcess():
                    #     complist=part.get_components()                    
                    #     for component in complist:
                    #         print("RRRRREEAAAAALLLY")
                    #         if component.hasProcess(process) and not((component.partnumber+component.rev)  in dupcheck):                            
                    #             processlist.append(component)
                    #             dupcheck.append(component.partnumber+component.rev)
                                
                    #             print((component.partnumber+component.rev)  in dupcheck)

        

        
        if str(processdict['purchaselist']).lower()=="yes" and len(processlist)>0:
            
            
            #Process folder
            processfolder=summaryfolder+"/Manufacturing - "+process+"/"
            create_folder_ifnotexists(processfolder)

            processbom=solidbom.solidbom_from_flatbom([Part.partFromDict(x) for x in processlist],part_in,
                                                    outputfolder=processfolder)
            #Get files
            for extension in processfiles:
                get_files(processbom.flatbom,extension,processfolder,subfolder=False)

            #Create visual list
            visualtitle=process.upper() + "-Checklist"
            #Create the visual list
            visuallist=visual_list(processbom, outputfolder=processfolder,title=visualtitle.replace(" ","_" ))

            #Create list with title
            bomtitle=bom_in.tag+"- scope of supply"
            # excel_list=bom_to_excel(processbom.flatbom,processfolder,title=process+"-"+ bomtitle,qty="qty", firstrow=1)
            excelbom=processbom.solidbom_to_excel(process=process)

  
    
    #################################
    # Fabrication steel loop
    ############################## 



    #Extract the welding components
    if part_in.hasProcess("welding"):
        manbom=[]
        # manbom.append(Part.partFromDict(part_in))
    else:
        manbom= [x for x in flatbom_dict if ( Part.partFromDict(x).hasProcess("welding") \
                                        or Part.partFromDict(x).hasProcess("lasercut") \
                                        or Part.partFromDict(x).hasProcess("folding") )]

    if manbom==[] and part_in.hasProcess("welding"):
        manbom.append(part_in.as_dict())
        


     
    tempsteellist=[]
    tempconsumedlist=[]

    existing=[]
    existingqty=[]
    if  len(manbom)>0:
        manbomPartType=[Part.partFromDict(x) for x in manbom]

        #Process folder
        manfolder=summaryfolder+"/Manufacturing - Steel/"
        create_folder_ifnotexists(manfolder)
        
        #Create the SolidBom class object for easier referencing, and override the output folder
        bom_inman=solidbom.solidbom_from_flatbom(manbomPartType,part_in)
        bom_inman.folderout=manfolder


        #Create visual list
        visualtitle="STEEL-Checklist"
        #Create the visual list
        visuallist=visual_list(bom_inman, outputfolder=manfolder,title=visualtitle)
        excelbom=bom_inman.solidbom_to_excel(process="steel")

       
        #Loop over the fabrication components and create files
       
        

        for index,component in enumerate(manbom):
            # print("********BEFORE***********")
            # for item in existing:
            #     print(item.qty, item)
            # print("*********************")

            #Get flatbom for each component
            com_flatbom=[]
            com_flatbom, consumed_flatbom=Part.partFromDict(component).get_components(components_only=False,
                                                    flatbomtodict=True,
                                                    existing=existing,existingqty=existingqty,
                                                    list_consumed=True,consumedtodict=True)
            com_flatbom.append(component)
            # print("con_flatbom", component.qty, component)

            # for conpart in consumed_flatbom:
            #     print ("%%%%",conpart['qty'],conpart['partnumber'],conpart['parent'])
            
            
            
            # existing=existing+com_flatbom
            for item in com_flatbom:

                try:
                    existing.append(copy.deepcopy(item))
                except:
                    existing.append(item)
                    print("copy drama with",item)
            existingqty=[item['qty'] for item in existing]

            # print(existingqty)

            re_flatbom=[]
            for item in com_flatbom:
                parto=Part.query.filter_by(partnumber=item['partnumber'],revision=item['revision']).first()
                parto.qty=item['qty']
                re_flatbom.append(parto)

                
                
            com_bom=solidbom.solidbom_from_flatbom(re_flatbom,Part.partFromDict(component))

            # #Get manufacturing files
            get_files(com_bom.flatbom,'dxf',manfolder,subfolder=False)
            if Part.partFromDict(component).hasProcess("welding"):
                try:
                    IndexPDF(com_bom,outputfolder=manfolder,savevisual=False,sort=True,showvisual=True)
                    print("uncomment the index")
                except:
                    print("************INDEX ERROR************************")
                    print(com_bom)
                    print("************INDEX ERROR************************")
                    
            else:
                get_files(com_bom.flatbom,'pdf',manfolder,subfolder=False)

            tempsteellist=tempsteellist+re_flatbom
            tempconsumedlist=tempconsumedlist+consumed_flatbom

            # print("*********************")
            # for item in existing:
            #     print(item.qty, item)
            # print("*********AFTER************")

        #Add top level part as refrence for first page and remove duplicates
        steellist=[part_in]
        [steellist.append(item) for item in tempsteellist if item not in steellist]

        #Create the lasercut and/or folding list
        cutlist=[x  for x in tempsteellist if x.hasProcess("lasercut") or x.hasProcess("folding") or x.hasProcess("cutting")]
        
        #Cutlist  for steeel manufacturing
        cutdict={"partnumber":[],"revision":[],"qty":[],"material":[],"description":[],"thickness":[],"pngpath":[],"finish":[]}
        pngfolder=fileserver_path+deliverables_folder+"png/"
        for item in cutlist:
            cutdict['partnumber'].append(item.partnumber)
            cutdict['revision'].append(item.revision)
            cutdict['qty'].append(item.qty)
            cutdict['description'].append(item.description)
            cutdict['material'].append(item.material)
            cutdict['thickness'].append(item.thickness)
            cutdict['finish'].append(item.finish)
            cutdict['pngpath'].append(pngfolder+item.partnumber+"_REV_"+item.revision+".png")
        cutpd=pd.DataFrame(cutdict)
        
        # cut_excel_list=bom_to_excel(cutpd,manfolder,title="Sheet Cutlist -"+ bom_inman.tag,qty="qty", firstrow=1)

        excelbom=solidbom.solidbom_from_flatbom(cutlist,Part.partFromDict(part_in),outputfolder=manfolder).solidbom_to_excel(process="cutlist")
        


        fab_to_remove_from_consumed=[x  for x in tempsteellist if x.hasProcess("lasercut") or x.hasProcess("welding") or x.hasProcess("folding") or x.hasProcess("cutting")]


        #Create the drawing pack (pdf)
        # if part_in.partnumber!="":
        #     steelbom=solidbom.solidbom_from_flatbom(steellist,part_in)
        #     steelpack=IndexPDF(steelbom,outputfolder=manfolder,sort=False,showvisual=False)

        #Create list with title
        # bomtitle=bom_in.tag+"- scope of supply"        
        # steelbom.flatbom=steelbom.flatbom[steelbom.flatbom.partnumber!=part_in.partnumber]  
        # excel_list=bom_to_excel(steelbom.flatbom,manfolder,title="Steel manufacturing -"+ bomtitle,qty="qty", firstrow=1)



    removefromconsumedlist=[]
    print("tempsteellisttempsteellisttempsteellisttempsteellisttempsteellisttempsteellisttempsteellisttempsteellist")
    for part in fab_to_remove_from_consumed:
        dicto=part.as_dict()
        d2 = copy.deepcopy(dicto)
        d2['parent']="from manbom"
        removefromconsumedlist.append(d2)
        print(d2['partnumber'])
    print("tempsteellisttempsteellisttempsteellisttempsteellisttempsteellisttempsteellisttempsteellisttempsteellist")


    for partcon in cleanconsumelist:        
        for part in removefromconsumedlist:            
            if partcon['partnumber']==part['partnumber'] and partcon['revision']==part['revision'] :
                partcon['qty']=partcon['qty']-part['qty']
    finalconsumedlist=[x for x in cleanconsumelist if x['qty']>0]

    

    print("finalconsumedlistfinalconsumedlistfinalconsumedlistfinalconsumedlistfinalconsumedlistfinalconsumedlist")
    for x in finalconsumedlist:
        print(x['partnumber'])
    print("finalconsumedlistfinalconsumedlistfinalconsumedlistfinalconsumedlistfinalconsumedlistfinalconsumedlist")




    ##Compute the consumed parts:
    
    if len(finalconsumedlist)>0:
            process="CONSUMED - NOT LISTED ELSEWHERE"
            consumed_bomflat=solidbom.solidbom_from_flatbom([Part.partFromDict(x) for x in finalconsumedlist],part_in)
            
            #Process folder
            processfolder=summaryfolder+"/Manufacturing - "+process+"/"
            create_folder_ifnotexists(processfolder)

            #Get files
            get_files(consumed_bomflat.flatbom,"pdf",processfolder,subfolder=False)
            get_files(consumed_bomflat.flatbom,"dxf",processfolder,subfolder=False)
            get_files(consumed_bomflat.flatbom,"step",processfolder,subfolder=False)

            #Create visual list
            visualtitle="Checklist for "+process
            #Create the visual list
            visuallist=visual_list(consumed_bomflat, outputfolder=processfolder,title=visualtitle.replace(" ","_" ))
 
            #Create list with title
            bomtitle=bom_in.tag+"- scope of supply"
            excel_list=bom_to_excel(consumed_bomflat.flatbom,processfolder,title=process+"-"+ bomtitle,qty="qty", firstrow=1)
            consumedflatbom=copy.deepcopy(consumed_bomflat.flatbom)


        
    
    #Create the excel bom
    try:
        excelbom=bom_in.solidbom_to_excel(consumed=consumedflatbom)
    except:
        excelbom=bom_in.solidbom_to_excel()
    
    # excelcutfoldbom=bom_in.solidbom_to_excel(process='cutfold')

    #Create the visual list
    visuallist=visual_list(bom_in, outputfolder=summaryfolder,
                title=("Scope of supply").replace(" ","_" ))

    
    #Create scope of supply 
    zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
    path, filename = os.path.split(zipfile)
    finalfile=fileserver_path+deliverables_folder+"temp/"+"PROCUREMENT PACKAGE-"+filename
    finalfile=finalfile.replace('.zip',"-"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S')+".zip")
    shutil.copy2(Path(zipfile),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)