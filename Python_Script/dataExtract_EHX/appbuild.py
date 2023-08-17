from cx_Freeze import setup, Executable

setup(
    name="thinkCore",
    version="0.1",
    description="Used to parse and build recipe data for Drexel",
    executables=[Executable(r"Python_Script\dataExtract_EHX\maintemp.py", base= None)]
)
