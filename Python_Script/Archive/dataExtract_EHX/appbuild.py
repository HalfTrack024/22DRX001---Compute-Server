from cx_Freeze import setup, Executable

import os
import sys
PYTHON_INSTALL_DIR = os.path.dirname(sys.executable)
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

include_files = [(os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'), os.path.join('lib', 'tk86t.dll')),
                 (os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'), os.path.join('lib', 'tcl86t.dll'))]
packages = ["idna","os","sys","sklearn","opcua","logging","psycopg2","numpy","stl", "PIL","xmltodict","pandas","matplotlib"]
options = {'build_exe' : {'packages':packages, 'include_files':include_files}}

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable(r"Python_Script\dataExtract_EHX\maintemp.py", base=base)]

setup(name="thinkcore",options=options,version="0.1",description="<any description>",executables=executables)