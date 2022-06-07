"""
The flask application package.
"""

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension


#SQL libraries
from flask_sqlalchemy import SQLAlchemy


import sqlite3

#System libraries
import os             #for opening the file after creation
import pandas as pd   #Dataframe libraries

#For web monitoring
import flask_monitoringdashboard as dashboard




#print("loaded init") 
###################################
################## SYSTEM SETUP
###################################

#Configuration strings
deliverables=["dxf","edr","edr_d","jpg","jpg_d","pdf","png","png_d","step"]
maincols=["partnumber","revision","description","material","process","process2","process3","finish"]
refcols=["approved","totalqty","mass","thickness", 'category','oem','supplier','supplier_partnumber',"datasheet","link"]

lowercase_properties=["process","process2","process3","finish","treatment"]
hardware_folder=['toolbox','browser']   


#Load configuration
package_directory = os.path.dirname(os.path.abspath(__file__))

def loadconfiguration(filein=package_directory+'/data/TinyMRP_conf.xlsm'):

    
    
    excelfile=pd.ExcelFile(filein)
    process_conf=excelfile.parse('process')
    property_conf=excelfile.parse('property')
    variables_conf=excelfile.parse('variables')
    processfields_conf=excelfile.parse('processfields')


    process_conf=process_conf.set_index('process').to_dict('index')
    property_conf=property_conf.set_index('property').to_dict('index')
    variables_conf=variables_conf.set_index('variable').to_dict('index')
    processfields_conf=processfields_conf.set_index('process').to_dict('index')

    fieldlist=[]
    fieldorder=[]
    
    

    for process in process_conf.keys():
        fieldlist=[]
        fieldorder=[]
        for property in property_conf.keys():
            try:
                if str(processfields_conf[process][property]).isalnum() and str(processfields_conf[process][property])!='nan':
                    ##print("value",processfields_conf[process][property] )
                    fieldlist.append({'prop':property,'order':str(processfields_conf[process][property])})
                    fieldorder.append(str(processfields_conf[process][property]))
            except:
                ##print("Issue with " , process , property)
                pass
        
        #Range the list so the print out is ordered
        def myFunc(e):
            return e['order']
        try:
            fieldlist.sort(key=myFunc)
        except:
            pass
            #print("Couldnt sort ",process)
        
        fieldlist= [x['prop'] for x in fieldlist]
        # #print(fieldlist)

        try:
            process_conf[process]['fields']=fieldlist
            #process_conf[process]['fieldsorder']=fieldorder
        except:
            # #print("List issue with " , process , property)
            pass
        ##print(process,fieldlist)


    ##print(process_conf)
    return [process_conf,property_conf,variables_conf]


########## IMPORTANT ENVIROMENT VARIABLES TO LOAD FROM THE EXCEL FILE
process_conf,property_conf, variables_conf = loadconfiguration()

main_folder=variables_conf['tinymrp']['value']
folderout=variables_conf['folderout']['value']
deliverables_folder=variables_conf['deliverables_folder']['value']
fileserver_path=variables_conf['fileserver_path']['value']
path_wkhtmltopdf=variables_conf['path_wkhtmltopdf']['value']
webfileserver=variables_conf['webfileserver']['value']
datasheet_folder=variables_conf['datasheet_folder']['value']
webserver=variables_conf['webserver']['value']





# create and configure the app




app = Flask(__name__, instance_relative_config=True)


#Add boostrap
bootstrap = Bootstrap(app)


#Monitor web module
dashboard.bind(app)
dashboard.config.init_from(file='/TinyMRP/TinyWEB/dasboard_config.cfg')


app.config['PROCESS_DESCRIPTION']=[ [x,
                                     process_conf[x]['icon'],
                                     process_conf[x]['color']] for x in process_conf.keys()]

processes=[]
icons=[]
colors=[]

for process in process_conf.keys():
    processes.append(process)
    icons.append(process_conf[process]['icon'])
    colors.append(process_conf[process]['color'])

app.config['PROCESS_LEGEND']=[ {'process':process,'icon':'images/'+icon,'color':color} for  (process,icon,color) in zip(processes,icons,colors) ]

#print (process_conf)
##print(app.config['PROCESS_LEGEND'])

app.config['PIC_LOCATION'] = fileserver_path+ deliverables_folder+"/pic"
app.config['REPORTS_PATH']=folderout


#app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['fileserver']=webfileserver
app.config['UPLOAD_PATH']='upload'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///data//TinyMRP.db'
app.SECRET_KEY = 'dev'
app.secret_key ='dev'
app.jinja_env.auto_reload = True
#app.config.from_mapping(
#    SECRET_KEY='dev',
#    DATABASE= 'I:\\SYNC\\PYTHON\\TinyMRP\\TinyMRP\\TinyWEB\\TinyWEB\\data\\TinyMRP.db',
#    #DATABASE=os.path.join(app.instance_path, '\\data\\TinyMRP.db'),
#)



#Debugging setup 
#app.debug=True
#app.config['DEBUG_TB_INTERCEPT_REDIRECTS']=False
#toolbar = DebugToolbarExtension(app)


db = SQLAlchemy(app)

import TinyWEB.views
