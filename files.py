# files.py, Charlie Jordan, 3/7/2025

import json
from pathlib import PurePath
import consts

def save_config(config_dict):
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    # @TODO do some checks here for contents?
    with open(config_path, 'w') as fp:
        json.dump(config_dict, fp, indent=2, default=path_default)

def path_default(obj):
    if isinstance(obj, PurePath):
        return str(obj)
    raise TypeError(f'Cannot serialize object of {type(obj)}')



def load_config():
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    try:
        with open(config_path, 'r') as fp:
            dict_ = json.load(fp)
            if 'psse_version' in dict_:
                set_psse_version(dict_['psse_version'][0])

            return dict_
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return None

def set_psse_version(major_version):
    new_suffix = consts.PSSE_EXE_SUFFIX.replace(
        '35.exe', f"{major_version}.exe"
    )
    consts.PSSE_EXE_SUFFIX = new_suffix

def save_history(history_dict):
    history_path = consts.EXE_DIR / consts.HISTORY_FILENAME
    with open(history_path, 'w') as fp:
        json.dump(history_dict, fp, indent=2)

def load_history():
    history_path = consts.EXE_DIR / consts.HISTORY_FILENAME
    try:
        with open(history_path, 'r') as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {}

def history_set(file, program):
    history = load_history()
    history[file] = program
    save_history(history)
