from distutils.core import setup
import py2exe

setup(
    console=['Python_Script\dataExtract_EHX\main.py'],
    options={
        'py2exe': {
            'bundle_files': 1,
            'compressed': True
        }
    },
    zipfile=None
)
