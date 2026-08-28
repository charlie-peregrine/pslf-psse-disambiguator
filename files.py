# files.py, Charlie Jordan, 3/7/2025

import json
import os
from pathlib import PurePath, Path
import time
from tkinter import messagebox
import tempfile
import traceback
import consts
import filelock
import shutil
import re
import logging

logger = logging.getLogger(__name__)


def save_config(config_dict):
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    # @TODO do some checks here for contents?
    with open(config_path, "w") as fp:
        json.dump(config_dict, fp, indent=2, default=path_default)
    logger.info("Config saved.")


def path_default(obj):
    if isinstance(obj, PurePath):
        return str(obj)
    raise TypeError(f"Cannot serialize object of {type(obj)}")


def load_config():
    config_path = consts.EXE_DIR / consts.CONFIG_FILENAME
    logger.info(f"Getting config file from {config_path}")
    try:
        with open(config_path, "r") as fp:
            dict_ = json.load(fp)
            if "psse_version" in dict_:
                set_psse_version(dict_["psse_version"][0])

            logger.info("Config loaded successfully.")
            for k, v in dict_.items():
                logger.info(f"configs: {k:>15} : {v}")
            return dict_
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.info("Config load failed. reason: %s", e)
        return None


def psse_exe_exists(config: dict):
    psse_path = Path(config["psse"]) / consts.PSSE_EXE_SUFFIX
    exists = psse_path.exists()
    if not exists:
        logger.warning(f"PSSE EXE DOES NOT EXIST")
    return exists


def pslf_exe_exists(config: dict):
    pslf_path = Path(config["pslf"]) / consts.PSLF_EXE_SUFFIX
    exists = pslf_path.exists()
    if not exists:
        logger.warning(f"PSLF EXE DOES NOT EXIST")
    return exists


def exes_exist(config: dict):
    return pslf_exe_exists(config) and psse_exe_exists(config)


def set_psse_version(major_version):
    new_suffix = re.sub(
        r"\d\d\.exe", str(major_version) + ".exe", consts.PSSE_EXE_SUFFIX, count=1
    )
    consts.PSSE_EXE_SUFFIX = new_suffix
    logger.info("psse version set to %s", major_version)
    logger.info("psse suffix set to %s", new_suffix)


def save_history(history_dict):
    history_path = consts.EXE_DIR / consts.HISTORY_FILENAME
    with open(history_path, "w") as fp:
        json.dump(history_dict, fp, indent=2)
    logger.info("History Saved")


def load_history():
    history_path = consts.EXE_DIR / consts.HISTORY_FILENAME
    try:
        with open(history_path, "r") as fp:
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


def _line_sort_key(x):
    y = re.search(r"[0-9:.]+", x)
    if y is not None:
        return y[0]
    else:
        return ""


class _TermLogHolder:
    def __init__(self, working_dir: str | Path):
        # check for term.log
        self.term_log_path = Path(working_dir) / "term.log"
        self.failed = False

        logger.info("TermLogHolder init")

        if self.term_log_path.exists():
            logger.info("term.log exists")
            try:
                term_stat = self.term_log_path.stat()
            except OSError as e:
                logger.info(f"Stat Failed: {e}")
                self._set_fail()
                return

            self.term_times = (term_stat.st_atime, term_stat.st_mtime)
            logger.info(f"term.log times: {self.term_times}")
            self.temp_dir = tempfile.TemporaryDirectory()
            try:
                shutil.copy2(self.term_log_path, self.temp_dir.name)
                logger.info("term.log temp copy successful")
            except OSError as e:
                logger.info(f"term.log temp copy failed: {e}")
                self._set_fail()
                return
        else:
            logger.info("term.log does not exist.")
            self.term_times = None
            self.temp_dir = None

    def _set_fail(self):
        self.term_times = None
        self.temp_dir = None
        self.failed = True

    def cleanup(self):
        try:
            logger.info("cleanup starting")
            self._cleanup()
            logger.info("cleanup finished")
        except Exception as e:
            logger.info(f"TermLogHandler cleanup exception: {e}")
        finally:
            if self.temp_dir is not None:
                try:
                    logger.info("Attemping temp dir cleanup")
                    self.temp_dir.cleanup()
                    logger.info("temp dir cleanup successfull")
                except OSError as e:
                    logger.info(f"Temp dir cleanup failed: {e}")

    def _cleanup(self):
        if self.failed:
            logger.info("TermLogHandler failed flag set. Aborting cleanup.")
            return
        if self.term_times is not None and self.temp_dir is not None:
            logger.info("term_times and temp_dir not None, copying back")
            # copy term log back and delete temp directory
            temp_term_log = Path(self.temp_dir.name) / self.term_log_path.name
            try:
                term_stat = self.term_log_path.stat()
            except OSError as e:
                logger.info(f"Stat Failed: {e}")
                raise

            if self.term_times != (term_stat.st_atime, term_stat.st_mtime):
                logger.info("New times different, copying back over.")
                try:
                    shutil.copy2(temp_term_log, self.term_log_path)
                    logger.info("term.log copied back")
                except OSError as e:
                    logger.info(f"copy2 failed: {e}")
                    raise
                try:
                    os.utime(self.term_log_path, self.term_times)
                    logger.info("term.log times reset")
                except OSError as e:
                    logger.info(f"os.utime failed: {e}")
                    raise
        else:
            logger.info("term_times and/or temp_dir is None, deleting term.log")
            try:
                # delete term log
                self.term_log_path.unlink()
                logger.info("term.log deleted")
            except OSError as e:
                logger.info(f"term log deletion failed: {e}")
                raise


def hold_term_log(working_dir) -> _TermLogHolder:
    return _TermLogHolder(working_dir)


# remove two day old logs and dangling log folders
def remove_old_logs():
    now = time.time()
    one_hour_ago = now - 3600
    two_days_ago = now - 2 * 86400
    for path in consts.LOGS_DIR.iterdir():
        try:
            ctime = path.stat().st_ctime
            if path.is_dir():
                if ctime < one_hour_ago:
                    shutil.rmtree(path)
            else:
                if ctime < two_days_ago:
                    os.remove(path)
        except OSError as e:
            print(f"Cant remove {path}")
            print(e)


def remix_logs():
    lines = []
    oserrors = []
    earliest_time = time.time()
    log_folder = consts.get_log_folder()
    for path in log_folder.glob("ppd?*.log"):
        earliest_time = min(earliest_time, int(path.stat().st_ctime))
        try:
            with open(path, "r") as fp:
                while line := fp.readline():
                    lines.append(line)
            os.remove(path)
        except OSError:
            oserrors.append(traceback.format_exc())

    lines.sort(key=_line_sort_key)
    ppd_log_name = consts.LOG_FILENAME.format(
        time.strftime("_%Y-%m-%d_%H-%M-%S", time.localtime(earliest_time))
    )
    merged_log = consts.LOGS_DIR / ppd_log_name
    try:
        with open(merged_log, "w") as fp:
            for line in lines:
                fp.write(line)
    except OSError:
        oserrors.append(traceback.format_exc())

    remove_old_logs()

    rmx_log_name = f"remix_error_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    rmx_log_path = consts.LOGS_DIR / rmx_log_name
    if oserrors:
        with open(rmx_log_path, "w") as fp:
            fp.write(rmx_log_name + "\n")
            for err in oserrors:
                fp.write("==========\n")
                fp.write(err)
                fp.write("\n")
        messagebox.showerror(
            title="Remix Logs Error",
            message=f"An error occured while remixing the ppd logs. Please attach remix_error.log, ppd.log, and the log{os.getpid()} directory in your PSLF/PSSE Disambiguator installation directory to your bug report.",
        )

    # copy the file to the exe directory to be nice to the user
    with filelock.FileLock(consts.LOG_COPY_LOCK_FILE):
        try:
            shutil.copy2(merged_log, consts.EXE_DIR / consts.LOG_FILENAME.format(""))
            if rmx_log_path.exists():
                shutil.copy2(rmx_log_path, consts.EXE_DIR / "remix_error.log")
        except:
            blah_txt = f" and '{rmx_log_path}'" if rmx_log_path.exists() else ""
            big_txt = "An error occurred copying some log files. Please include '{}'{} in your bug report."
            messagebox.showerror(
                title="Remix Logs Error", message=big_txt.format(merged_log, blah_txt)
            )
