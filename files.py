# files.py, Charlie Jordan, 3/7/2025

import json
import os
from pathlib import PurePath
import consts
import re
import logging
logger = logging.getLogger(__name__)

def save_config(config_dict):
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    # @TODO do some checks here for contents?
    with open(config_path, 'w') as fp:
        json.dump(config_dict, fp, indent=2, default=path_default)
    logger.info("Config saved.")

def path_default(obj):
    if isinstance(obj, PurePath):
        return str(obj)
    raise TypeError(f'Cannot serialize object of {type(obj)}')

def load_config():
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    logger.info(f"Getting config file from {config_path}")
    try:
        with open(config_path, 'r') as fp:
            dict_ = json.load(fp)
            if 'psse_version' in dict_:
                set_psse_version(dict_['psse_version'][0])

            logger.info("Config loaded successfully.")
            for k, v in dict_.items():
                logger.info(f"configs: {k:>15} : {v}")
            return dict_
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.info("Config load failed. reason: %s", e)
        return None

def set_psse_version(major_version):
    new_suffix = re.sub(
        r'\d\d\.exe',
        str(major_version) + ".exe",
        consts.PSSE_EXE_SUFFIX,
        count=1
    )
    consts.PSSE_EXE_SUFFIX = new_suffix
    logger.info("psse version set to %s", major_version)
    logger.info("psse suffix set to %s", new_suffix)

def save_history(history_dict):
    history_path = consts.EXE_DIR / consts.HISTORY_FILENAME
    with open(history_path, 'w') as fp:
        json.dump(history_dict, fp, indent=2)
    logger.info("History Saved")

def load_history():
    history_path = consts.EXE_DIR / consts.HISTORY_FILENAME
    try:
        with open(history_path, 'r') as fp:
            d = json.load(fp)
            logger.info("History Loaded successfully")
            return d
    except FileNotFoundError as e:
        logger.info("History loading failed. reason: %s", e)
        return {}

def history_set(file, program):
    history = load_history()
    history[file] = program
    save_history(history)
    logger.info("Added {%s : %s} to history", file, program)

def remix_logs():
    lines = []
    for path in consts.EXE_DIR.glob('ppd?*.log'):
        with open(path, 'r') as fp:
            while line := fp.readline():
                lines.append(line.rstrip())
        os.remove(path)
        # print(path)
    def key_(x):
        y = re.search(r"[0-9:.]+", x)
        if y is not None:
            return y[0]
        else:
            return ''
    lines.sort(key=key_)
    with open(consts.EXE_DIR / 'ppd.log', 'w') as fp:
        fp.write('\n'.join(lines))