
from subprocess import call
from pkgutil import iter_modules

def install_package(name):
    if name not in [tuple_[1] for tuple_ in iter_modules()]:
        call(["pip", "install", name])

install_package('datetime')
install_package('flask')
install_package('os')
install_package('chardet')
install_package('re')
install_package('shutil')
install_package('glob')
install_package('pickle')
install_package('pathlib')
install_package('pandas')
install_package('numpy')
install_package('sqlite3')
install_package('sqlalchemy')
install_package('openpyxl')
install_package('reportlab')
install_package('svglib')
install_package('PIL')
install_package('flask_sqlalchemy')
install_package('fnmatch')
install_package('PyPDF2')
install_package('fsspec')
install_package('pdfkit')
install_package('ifaddr')
install_package('pyperclip')
install_package('flask_bootstrap')
install_package('flask_uploads')

"""
Windows
Download the installer from the wkhtmltopdf downloads list and add folder with wkhtmltopdf binary to PATH.
"""



