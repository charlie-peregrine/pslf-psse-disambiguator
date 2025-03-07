# files.py, Charlie Jordan, 3/7/2025

import json

import consts

def save_config(config_dict):
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    # @TODO do some checks here for contents?
    with open(config_path, 'w') as fp:
        json.dump(config_dict, fp, indent=2)

def load_config():
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    try:
        with open(config_path, 'r') as fp:
            return json.load(fp)
    except FileNotFoundError:
        return None

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
