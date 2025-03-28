# PPDWindow.py, Charlie Jordan, 3/13/2025

import subprocess
from pathlib import Path
import multiprocessing
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
import logging
from PIL import Image, ImageTk
from PIL.Image import Resampling
from win32comext.shell import shell, shellcon
import threading
logger = logging.getLogger(__name__)


import files
import checks
import consts

# program constants for which column each program goes in the interface
pslf_col = 0
psse_col = 1
other_col = 2

ICON_SIZE = (128, 128)

class PPDWindow(tk.Tk):
    def __init__(self, file: str, configs: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = file
        self.configs = configs
        self.skip_prompt = self.configs['skip_prompt']
        self.after_code = ''
        self.key_bind_id = ''

        self.option_add('*tearOff', tk.FALSE)
        self.title("PSLF/PSSE Disambiguator")
        self.iconphoto(True, tk.PhotoImage(file=consts.IMG_DIR / "ppd.png"))
        self.config(bg=consts.BG_COLOR)
        self.resizable(False, False)
        self.wm_protocol("WM_DELETE_WINDW", self.close_callback)
        self.bind("<Escape>", self.close_callback)
        style = ttk.Style()
        style.configure(".", background=consts.BG_COLOR)

        
        self.hint_label = ttk.Label(self, text="Loading...\n\nHINT: You can press Control during load to manually disambiguate.",
                                    padding=25, justify='center')
        self.hint_label.grid(row=0, column=0)
        self.built = False

        self.open_result = ''
        self.open_thread = threading.Thread(target=self._open_check)
        self.open_thread.start()
        self.check_after_code = ''

        ### setup for control press if necessary
        logger.info("self.skip_prompt: %s", self.skip_prompt)
        if self.skip_prompt:
            # wait a little for a ctrl press
            self.focus_force()
            self.key_bind_id = self.bind("<Key>", self.key_bind)
            self.after_code = self.after(self.configs['wait_ms'], self.handle_check_results)
            logger.info("Bind and after created")
        else:
            # run checks immediately, show prompt here
            logger.info("Building")
            self.build()
            logger.info("Running Checks")
            self.handle_check_results()

    def build(self):
        #                    
        #                    
        #    button e   button f  button other
        #          hist line    
        #          bytes line   
        #          open line    
        #                    
        #                    
        
        self.hint_label.destroy()
        
        # pslf line with icon, entry, select button
        pslf_image = Image.open(consts.IMG_DIR / "pslf.png").resize(ICON_SIZE, Resampling.BICUBIC)
        self.pslf_icon = ImageTk.PhotoImage(pslf_image)
        psse_image = Image.open(consts.IMG_DIR / "psse.png").resize(ICON_SIZE, Resampling.BICUBIC)
        self.psse_icon = ImageTk.PhotoImage(psse_image)
        other_image = Image.open(consts.IMG_DIR / "other.png").resize(ICON_SIZE, Resampling.NEAREST)
        self.other_icon = ImageTk.PhotoImage(other_image)
        
        self.pslf_button = ttk.Button(self, image=self.pslf_icon,
                compound='top', text="Open PSLF",
                command=lambda: (self.destroy_and_run('pslf')))
        self.pslf_button.grid(row=1, column=0)
        self.psse_button = ttk.Button(self, image=self.psse_icon,
                compound='top', text="Open PSSE",
                command=lambda: (self.destroy_and_run('psse')))
        self.psse_button.grid(row=1, column=1)
        self.other_button = ttk.Button(self, image=self.other_icon,
                compound='top', text="Open Another Program",
                command=self.pick_new_program)
        self.other_button.grid(row=1, column=2)
        
        short_file = Path(self.file).name
        self.top_label = ttk.Label(self,
                justify='center', wraplength=(ICON_SIZE[0]+16)*3,
                text=f"Choose a program to open {short_file}. "
                "The text below the buttons shows information about the 3 checks "
                "that the disambiguator runs automatically.")
        self.top_label.grid(row=0, column=0, columnspan=3)
        
        self.hist_label = ttk.Label(self, text="history", justify='center',
                wraplength=ICON_SIZE[0]+8)
        self.hist_label.grid(row=2, column=0)
        self.bytes_label = ttk.Label(self, text="bytes", justify='center',
                wraplength=ICON_SIZE[0]+8)
        self.bytes_label.grid(row=3, column=1)
        self.open_label = ttk.Label(self, text="open", justify='center',
                wraplength=ICON_SIZE[0]+8)
        self.open_label.grid(row=4, column=2)
        
        for widget in self.winfo_children():
            widget.grid_configure(padx=4, pady=3)
        
        self.built = True

    def wait_for_open_thread(self):
        if self.open_thread.is_alive():
            logger.info("Waiting for open thread")
            self.check_after_code = self.after(100, self.wait_for_open_thread)
            return
        logger.info("Done waiting for open thread")
        self.open_thread.join()
        
        if self.skip_prompt and self.open_result:
            self._run_from_check(self.file, self.open_result, save_history=True)
            return
        
        self.open_label.config(wraplength=ICON_SIZE[0]+8)
        self.open_label.grid_configure(columnspan=1)

        if self.configs['use_python']:
            if self.open_result == 'pslf':
                position_label(self.open_label, pslf_col)
                self.open_label.config(text=f"Opening the SAV in PSLF succeeded.")
            elif self.open_result == 'psse':
                position_label(self.open_label, psse_col)
                self.open_label.config(text=f"Opening the SAV in PSSE succeeded.")
            else:
                # text says can't find a program
                position_label(self.open_label, other_col)
                self.open_label.config(text=f"Opening the SAV in PSLF and PSSE failed.")
        else:
            position_label(self.open_label, other_col)
            self.open_label.config(text=f"PPD not configured to use python APIs.")
        logger.info("wait_for_open_thread finished.")

    def close_callback(self, e=None):
        logger.info("Closing PPD")
        if self.check_after_code:
            logger.info("Stopping after")
            self.after_cancel(self.check_after_code)
        logger.info("Destroying window")
        self.destroy()
        logger.info("Joining open thread")
        self.open_thread.join()
        logger.info("Done closing PPD")
    
    def _open_check(self):
        # if this is the right version to use the python libraries then check
        # if the program can be run with those.
        self.open_result = ''
        if self.configs['use_python']:
            logger.info("running open_check.")
            self.open_result = checks.open_check(self.file)
            logger.info(f"open_check result: '{self.open_result}'")
            if self.open_result:
                logger.info(f"Successful open check")
        else:
            logger.info("skipping open_check.")
        
    def _run_from_check(self, file, prog, save_history=False):
        logger.info(f"Starting {file} in {prog}")
        if save_history:
            files.history_set(file, prog)
        run_program(prog, file)
        self.destroy()
    
    def handle_check_results(self):
        # open history and check if the file is there
        hist_result = checks.history_check(self.file)
        logger.info(f"history_check result: '{hist_result}'")
        if self.skip_prompt and hist_result:
            logger.info(f"Successful history check")
            self._run_from_check(self.file, hist_result)
            return
        
        # check the header bytes
        bytes_result = checks.bytes_check(self.file)
        logger.info(f"bytes_check result: '{bytes_result}'")
        if self.skip_prompt and bytes_result:
            logger.info(f"Successful bytes check")
            self._run_from_check(self.file, bytes_result, save_history=True)
            return
        
        if not self.built:
            self.build()

        # if we're here then we use the program responses to determine
        # what to put in the labels and where to place them

        # history check may have a different program in it and we need more logic
        # to account for that.
        if hist_result:
            prog = ''
            col = 0
            if hist_result == 'pslf':
                prog = 'PSLF'
                col = pslf_col
            elif hist_result == 'psse':
                prog = 'PSSE'
                col = psse_col
            else:
                prog = Path(hist_result).stem
                col = other_col
                # add menu to other_button to allow choice between rerunning and
                # choosing a new option
                menu = tk.Menu(self.other_button)
                menu.add_command(label=f"Open with {prog}",
                        command=lambda p=hist_result: (self.destroy_and_run(p)))
                menu.add_command(label=f"Choose another program...", command='')
                self.other_button.config(command=lambda: menu.post(*self.winfo_pointerxy()))

            self.hist_label.config(text=f"Recently opened with {prog}")
            position_label(self.hist_label, col)
        else:
            # text says can't find a program
            position_label(self.hist_label, other_col)
            self.hist_label.config(text="Previous program not found in history.")
        
        if bytes_result == 'pslf':
            position_label(self.bytes_label, pslf_col)
            self.bytes_label.config(text=f"SAV leading bytes check: PSLF")
        elif bytes_result == 'psse':
            position_label(self.bytes_label, psse_col)
            self.bytes_label.config(text=f"SAV leading bytes check: PSSE")
        else:
            position_label(self.bytes_label, other_col)
            self.bytes_label.config(text=f"SAV leading bytes check failed.")

        # set the label to show waiting text and then wait for the
        # open_check to finish
        self.open_label.config(wraplength=(ICON_SIZE[0]+16)*3,
                text="Waiting for the PSLF and PSSE checks to finish...")
        self.open_label.grid_configure(column=pslf_col, columnspan=3)
        self.deiconify()
        self.wait_for_open_thread()
            
        
    def destroy_and_run(self, program: str):
        logger.info("Entering destroy and run")
        self.destroy()
        run_program(program, self.file)
        hist = files.load_history()
        if self.file not in hist or hist[self.file] != program:
            logger.info("Adding to history")
            files.history_set(self.file, program)
        logger.info("Exitting destroy and run")
    
    def key_bind(self, e: tk.Event):
        logger.info("Event: %s", e)
        if e.keysym.lower().startswith("control"):
            self.unbind("<Key>", self.key_bind_id)
            self.after_cancel(self.after_code)
            self.skip_prompt = False
            self.withdraw()
            self.handle_check_results()
    
    def pick_new_program(self):
        startmenu_folder = shell.SHGetSpecialFolderPath(0,shellcon.CSIDL_COMMON_STARTMENU)
        startmenu_path = Path(startmenu_folder) / "Programs" 
        if not (startmenu_folder and startmenu_path.exists()):
            logger.error("Can't get start menu from win32 shell.")
            logger.error("shell returns: %s", startmenu_folder)
            logger.error("programs path: %s", startmenu_path)
            startmenu_path = Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs")
            if not startmenu_path.exists():
                logger.error("Can't find start menu folder")
                messagebox.showerror("Can't find Start Menu folder",
                        message="Can't find Start Menu folder. Please include ppd.log in your bug report.")
                return
        logger.info("Start menu path: %s", startmenu_path)
        logger.info("Asking for program")
        fname = askopenfilename(initialdir=startmenu_path, parent=self,
                title="Select a program from the start menu folder to open this file")
        logger.info(f"Program selected: '{fname}'")
        if fname:
            fpath = Path(fname)
            if fpath.exists():
                files.history_set(self.file, str(fpath))
                logger.info(f"Running '{self.file}' in '{fpath}")
                run_program(str(fpath), self.file)
                self.destroy()
            else:
                logger.info("Program selected does not exist.")
                messagebox.showerror("Program selected does not exist",
                        message=f"Program selected does not exist. '{fpath}'")
        else:
            logger.info("No program selected.")
            
def position_label(label: ttk.Label, col: int):
    label.grid_configure(column=col)

def run_program(program, file):
    # add a process layer to avoid directory change effects
    p = multiprocessing.Process(target=_run_program, args=(program, file))
    p.start()
    p.join()

def _run_program(program, file):
    command_format = 'cd "{work_dir}" & "{exe}" "{file}"'
    work_dir = str(Path(file).parent)
    logger.info("run_program start")
    
    def popen(cmd):
        return subprocess.Popen(cmd,shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    if program == 'pslf':
        suffix = consts.PSLF_EXE_SUFFIX
    elif program == 'psse':
        suffix = consts.PSSE_EXE_SUFFIX
    else:
        command_text = command_format.format(
            work_dir=work_dir, exe=program, file=file
        )
        logger.info("Generic command text: %s", command_text)

        logger.info("Starting subprocess.")
        p = popen(command_text)
        logger.info("Subprocess started.")
        return p
    
    config = files.load_config()
    if config is None:
        raise KeyError("Configuration file not found")
    
    exe = Path(config[program]) / suffix
    command_text = command_format.format(work_dir=work_dir, exe=exe, file=file)
    logger.info(program + " command_text: " + command_text)
    
    logger.info("Starting subprocess.")
    p = popen(command_text)
    logger.info("Subprocess started.")
    import os
    logger.info("os.getcwd(): %s", os.getcwd())
    return p
