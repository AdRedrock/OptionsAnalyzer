from pathlib import Path
import os.path
import sys

def is_nuitka() -> bool:
    """
    Check if the script is compiled with Nuitka.
    """
    is_nuitka = "__compiled__" in globals()
    is_nuitka2 = "NUITKA_ONEFILE_PARENT" in os.environ
    return is_nuitka or is_nuitka2

def get_data_dir() -> str:
    # Get current path to the binary:

    if is_nuitka():

        abs_pth = os.path.abspath(sys.argv[0])
        exe_dir = os.path.dirname(abs_pth)
        return  Path(exe_dir) / 'data'

    else:

        return Path(__file__).resolve().parent.parent.parent / 'data'

def get_data_dir_imported():
    return get_data_dir() / 'imported'

def get_global_dir():
    return Path(__file__).resolve().parent.parent.parent