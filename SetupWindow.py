# SetupWindow.py, Charlie Jordan, 3/10/2025

import importlib.util
import re

import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageTk
from PIL.Image import Resampling
from itertools import chain
import multiprocessing
import logging
logger = logging.getLogger(__name__)


import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from idlelib.tooltip import Hovertip
from textwrap import wrap as wraptext

import consts
import files

setup_text = ("This is the Setup window for PSLF/PSSE Disambiguator (PPD). "
            "PPD uses 3 checks to determine which program to open a SAV "
            "file with (hover for more info). After setup is over the "
            "program will automatically associate files ending in .sav "
            "with this program, and you will be able to run PPD "
            "directly by clicking a SAV file anywhere on your system. "
            "Please follow the steps below to set up the program.")
hover_text = ("The checks, performed in order are:\n1. A history check. The "
            "program stores a history of files opened with this program and "
            "which program the file was opened with. This allows the program "
            "to also be used to always open a specific file with a different "
            "program (e.g. many videogames also use the .sav file extension "
            "internally, and you might want to open those with a text editor "
            "instead of PSLF).\n2. A bytes check. The "
            "leading ~16 bytes of a SAV file contains information that is "
            "unique to the program that created it. By comparing the bytes "
            "from the SAV files to to known byte strings we can determine "
            "which program to open the file with.\n3. An open check. "
            "The last and slowest check that is run is an open check. This "
            "check just tries opening the sav file in both programs, using "
            "the published python api's for the two programs, and whichever "
            "program successfully opens the file is the correct program. This "
            "check happens in the background.")

class SetupWindow(tk.Tk):
    def __init__(self, configs):
        super().__init__()
        
        self.title(f"PSLF/PSSE Disambiguator Setup, Version {consts.VERSION}")
        self.wm_protocol("WM_DELETE_WINDW", self.cancel_command)
        
        self.iconphoto(True, tk.PhotoImage(file=consts.IMG_DIR / "ppd.png"))
        # self.minsize(450, 200)
        # self.geometry("400x200")
        # self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        if configs is None:
            self.configs = {}
            self.configs['pslf'] = consts.DEFAULT_PSLF_DIR_PATH
            self.configs['psse'] = consts.DEFAULT_PSSE_DIR_PATH
            self.configs['psse_version'] = (-1, -1, -1)
            self.configs['skip_prompt'] = True
            self.configs['use_python'] = False
            self.configs['wait_ms'] = 475
        else:
            self.configs = configs
            self.configs['pslf'] = Path(self.configs['pslf'])
            self.configs['psse'] = Path(self.configs['psse'])
        self.done = False
        
        
        ### booleans for making sure that everything that needs to happen happens
        self.has_valid_pslf = False
        self.has_valid_psse = False
        self.checked_py_libraries = False
        
        # after call code and queue
        self.queue = multiprocessing.Queue()
        self.start_after_code = ''
        self.proc_after_code = ''
        self.procs = []
        self.process_listener()
        
        
        style = ttk.Style()
        self.config(bg=consts.BG_COLOR)
        style.element_create('Labelframe.border', "from", 'alt')
        # below would be necessary if this were a different style name
        # style.layout('TLabelframe', [
        #     ('Labelframe.border', {'sticky' : 'nsew'})
        # ])
        style.configure('TLabelframe', relief='solid', bordercolor='slategrey', borderwidth=1)
        style.configure(".", background=consts.BG_COLOR)
        style.configure("BadEntry.TEntry", fieldbackground='lightred')
        style.configure("GoodEntry.TEntry", fieldbackground='lightgreen')
        
        self.top_label = ttk.Label(self, wraplength=450, justify='left',
                text=setup_text)
        self.top_label.grid(row=0, column=0, padx=3, pady=3)
        text_ls = ["\n".join(wraptext(t, 150)) for t in hover_text.split("\n")]
        text = "\n".join(text_ls)
        Hovertip(self.top_label, text=text, hover_delay=500)

        # buttons to save and close
        ### Button Frame
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=4, column=0, sticky='ew')
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        sep = ttk.Separator(self.button_frame, orient='horizontal')
        sep.grid(row=0, column=0, columnspan=2, sticky='ew')
        
        self.ok_button = ttk.Button(self.button_frame, text="OK",
                command=self.ok_command)
        self.ok_button.grid(row=2, column=0, sticky='ew')
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel",
                command=self.cancel_command)
        self.cancel_button.grid(row=2, column=1, sticky='ew')
        
        ### labelframe for setting directories
        self.exe_frame = ttk.LabelFrame(self, text="Step 1: Program Directories")
        self.exe_frame.grid(row=1, column=0, sticky='ew', padx=3, pady=3)
        self.exe_frame.columnconfigure(1, weight=1)

        self.exe_label = ttk.Label(self.exe_frame, wraplength=450, justify='left',
                text="Use the entries below to verify that the program has found the correct locations and versions of PSLF and PSSE. ")
        self.exe_label.grid(row=0, column=0, columnspan=3)

        icon_size = (16, 16)
        # pslf line with icon, entry, select button
        image = Image.open(consts.IMG_DIR / "pslf.png").resize(icon_size, Resampling.BICUBIC)
        self.pslf_icon = ImageTk.PhotoImage(image)
        self.pslf_icon_label = ttk.Label(self.exe_frame, compound='left', text='PSLF:', image=self.pslf_icon)
        self.pslf_icon_label.grid(row=1, column=0)
        
        pslf_v_cmd = (self.register(self.pslf_validate), '%P')
        self.pslf_entry = tk.Entry(self.exe_frame, validate='key',
                validatecommand=pslf_v_cmd, width=45)
        self.pslf_entry.insert(0, str(self.configs['pslf'] / consts.PSLF_EXE_SUFFIX))
        self.pslf_entry.grid(row=1, column=1, sticky='ew')
        self.pslf_select_button = ttk.Button(self.exe_frame, text="Select",
                command=self.pslf_select_button_callback)
        self.pslf_select_button.grid(row=1, column=2)
        
        # psse line with icon, entry, select button
        image = Image.open(consts.IMG_DIR / "psse.png").resize(icon_size, Resampling.BICUBIC)
        self.psse_icon = ImageTk.PhotoImage(image)
        self.psse_icon_label = ttk.Label(self.exe_frame, compound='left', text='PSSE:', image=self.psse_icon)
        self.psse_icon_label.grid(row=2, column=0)

        psse_v_cmd = (self.register(self.psse_validate), '%P')
        self.psse_entry = tk.Entry(self.exe_frame, validate='key',
                validatecommand=psse_v_cmd, width=45)
        self.psse_entry.insert(0, str(self.configs['psse'] / consts.PSSE_EXE_SUFFIX))
        self.psse_entry.grid(row=2, column=1, sticky='ew')
        self.psse_select_button = ttk.Button(self.exe_frame, text="Select",
                command=self.psse_select_button_callback)
        self.psse_select_button.grid(row=2, column=2)

        ### Labelframe for misc options
        self.misc_frame = ttk.LabelFrame(self, text="Step 2: Preferences and Hints")
        self.misc_frame.grid(row=2, column=0, sticky='ew', padx=3, pady=3)
        self.misc_frame.columnconfigure(1, weight=1)

        # skip prompt checkbox
        self.show_prompt_var = tk.BooleanVar(value=False)
        if 'skip_prompt' in self.configs:
            self.show_prompt_var.set(not self.configs['skip_prompt'])
        self.show_prompt_checkbox = ttk.Checkbutton(self.misc_frame, variable=self.show_prompt_var)
        self.show_prompt_checkbox.grid(row=0, column=0)
        self.show_prompt_label = ttk.Label(self.misc_frame, wraplength=400,
                text="Show a prompt to pick which program to run for a SAV file regardless of the automatically detected type. If unsure, it is highly recommended to leave this box unchecked.",
                justify='left')
        self.show_prompt_label.grid(row=0, column=1, sticky='w')
        
        # hint about hold control to show window regardless of skip prompt
        self.hint_label = ttk.Label(self.misc_frame, wraplength=450,
                text="HINT: If you left the box above unchecked you can still access the prompt by holding Control while the disambiguator is loading after opening a SAV file.",
                justify='left')
        self.hint_label.grid(row=1, column=0, columnspan=2, sticky='w')
        
        
        # Status for using python libraries
        sep = ttk.Separator(self.misc_frame, orient='horizontal')
        sep.grid(row=2, column=0, columnspan=2, sticky='ew')
        self.py_library_label = ttk.Label(self.misc_frame, wraplength=450,
                text="Checking Python Library Status...", justify='left')
        self.py_library_label.grid(row=3, column=0, columnspan=2, sticky='w')
        
        ### History Labelframe
        # self.history_frame = ttk.LabelFrame(self, text="Step 3: History")
        # self.history_frame.grid(row=0, column=1, rowspan=2, padx=3, pady=3)
        # clear history, remove from history, edit history? 
        
        for frame in (self.exe_frame, self.misc_frame, self.button_frame):
            for widget in frame.winfo_children():
                widget.grid_configure(padx=4, pady=3)
        self.show_prompt_checkbox.grid_configure(padx=(12, 0))

    def process_listener(self):
        if not self.queue.empty():
            good_str = (
                "The program will be able to use the PSLF and PSSE python "
                "APIs to disambiguate SAV files in addition to the other methods."
            )
            bad_str = (
                "The program won't be able to use the PSLF and PSSE python "
                "APIs to disambiguate SAV files. If you have a higher version "
                "installed then select that, otherwise don't worry, the "
                "python APIs are not strictly necessary. Reason(s): "
            )
            str_ = good_str
            good = False
            while not self.queue.empty():
                obj = self.queue.get()
                if isinstance(obj, list):
                    str_ = "INFO: " + bad_str + ' '.join(obj)
                    good = False
                    self.update_ok_button()
                else:
                    # obj is a boolean
                    if obj:
                        good = True
                        str_ = "INFO: " + good_str
                    else:
                        for p in self.procs:
                            p.join()
                        return
            self.configs['use_python'] = good
            self.checked_py_libraries = True
            self.update_ok_button()
            logger.info("Setting py_library_label to %s", str_)
            self.py_library_label.config(text=str_)
        remove_procs = []
        for p in self.procs:
            if not p.is_alive():
                p.join()
                remove_procs.append(p)
        for p in remove_procs:
            self.procs.remove(p)
        self.proc_after_code = self.after(200, self.process_listener)
            
    
    def pslf_validate(self, text):
        # check that the exe files exist
        # print(text)
        self.has_valid_pslf = False
        self.update_ok_button()
        dir_path = Path(text)
        if dir_path.exists():
            for parent in chain((dir_path,), dir_path.parents):
                pslf_exe_path = parent / consts.PSLF_EXE_SUFFIX
                if pslf_exe_path.exists():
                    self.configs['pslf'] = parent
                    self.start_after()
                    self.pslf_entry.config(background='lightgreen')
                    self.has_valid_pslf = True
                    self.update_ok_button()
                    return True
        
        self.pslf_entry.config(background='#FF6A6A')
        return True
    
    def pslf_select_button_callback(self):
        path = self.configs['pslf'] / consts.PSLF_EXE_SUFFIX
        file_name = fd.askopenfilename(
            initialdir=self.configs['pslf'],
            initialfile=path.name,
            filetypes=[("All Files", "*.*"), ("Executables", "*.exe")],
            defaultextension=".exe",
            title="Select Pslf.exe in the GE PSLF installation directory."
        )
        if file_name is not None:
            self.pslf_entry.delete(0, 'end')
            self.pslf_entry.insert(0, str(Path(file_name)))

    def psse_select_button_callback(self):
        path = self.configs['psse'] / consts.PSSE_EXE_SUFFIX
        file_name = fd.askopenfilename(
            initialdir=path.parent,
            initialfile=path.name,
            filetypes=[("All Files", "*.*"), ("Executables", "*.exe")],
            defaultextension=".exe",
            title="Select psse##.exe in the PSSE installation directory."
        )
        if file_name is not None:
            self.psse_entry.delete(0, 'end')
            self.psse_entry.insert(0, str(Path(file_name)))

    def psse_validate(self, text):
        # check that the exe files exist
        # print(text)
        
        self.has_valid_psse = False
        self.update_ok_button()
        dir_path = Path(text)
        if dir_path.exists():
            for parent in chain((dir_path,), dir_path.parents):
                version = get_psse_version(parent)
                if version is not None:
                    files.set_psse_version(version[0])
                    self.configs['psse_version'] = version
                    psse_exe_path = parent / consts.PSSE_EXE_SUFFIX
                    if psse_exe_path.exists():
                        self.configs['psse'] = parent
                        self.start_after()
                        self.psse_entry.config(background='lightgreen')
                        self.has_valid_psse = True
                        self.update_ok_button()
                        return True
        
        self.psse_entry.config(background='#FF6A6A')
        return True
    
    def start_after(self):
        if self.start_after_code:
            self.after_cancel(self.start_after_code)
            self.start_after_code = ''
        self.start_after_code = self.after(300, self.start_check_py_lib)
    
    def start_check_py_lib(self):
        self.start_after_code = ''
        p = multiprocessing.Process(
            target=check_py_library_usability,
            args=(self.configs['pslf'], self.configs['psse'], self.queue),
            daemon=True
        )
        self.procs.append(p)
        p.start()
    
    def update_ok_button(self):
        self.ok_button
        is_valid = self.has_valid_pslf and \
                   self.has_valid_psse and \
                   self.checked_py_libraries
        if is_valid:
            self.ok_button.config(state='normal')
        else:
            self.ok_button.config(state='disabled')
    
    def ok_command(self):
        self.destroy()
        # save configuration
        self.configs['skip_prompt'] = not self.show_prompt_var.get()
        files.save_config(self.configs)
        if not files.load_history():
            files.save_history({})
        
        # set fta here
        if consts.IS_BUNDLED:
            logger.info("Setting file type association")
            set_file_type_association(sys.executable, "ppd.ico", ".sav")
        else:
            logger.info("skipping set fta for unbundled files")
        
        # done tag for letting other stuff run properly after this window is closed
        self.done = True
        # finish active threads
        self.stop_process_listener()

    def cancel_command(self):
        self.stop_process_listener()
        self.destroy()

    def stop_process_listener(self):
        self.queue.put(False)
        self.after_cancel(self.proc_after_code)
        self.process_listener()

def check_py_library_usability(
    pslf_dir: Path | str, psse_dir: Path | str, q: multiprocessing.Queue
):
    pslf_dir = Path(pslf_dir)
    psse_dir = Path(psse_dir)
    pslf_py_path = pslf_dir / consts.PSLF_PY_SUFFIX
    psse_py_path = psse_dir / consts.PSSE_PY_SUFFIX
    
    # add paths to import search paths
    sys.path.append(str(pslf_py_path.parent))
    sys.path.append(str(psse_py_path.parent))
    
    messages = []
    vers = sys.version_info[:2]
    if vers != (3, 11):
        messages.append(
            f"Invalid python version ({vers[0]}.{vers[1]}) to use python libraries.")
        logger.info(messages[-1])
    else:
        if not is_valid_pslf_version(pslf_dir / consts.PSLF_EXE_SUFFIX):
            messages.append("Invalid PSLF version for python libraries. Need PSLF 23.1.0 or greater.")
            logger.info(messages[-1])
        elif importlib.util.find_spec('PSLF_PYTHON') is None:
            messages.append("Can't find PSLF python libraries in directory.")
            logger.info(messages[-1])
        if not is_valid_psse_version(psse_dir):
            messages.append("Invalid PSSE version for python libraries. Need PSSE 35.6.2 or greater.")
            logger.info(messages[-1])
        elif importlib.util.find_spec('psse35') is None:
            messages.append("Can't find PSSE python libraries in directory.")
            logger.info(messages[-1])
    
    # below not necessary in its own process
    # sys.path.remove(str(pslf_py_path.parent))
    # sys.path.remove(str(psse_py_path.parent))
    
    q.put(messages or True)



def is_valid_pslf_version(path_to_exe: Path):
    # use 'Pslf.exe --version' and checkoutput to see if version is greater than or equal to 23.1.0
    if path_to_exe.exists():
        p = subprocess.run(f'"{path_to_exe}" --version', stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        output = p.stdout
        match_ = re.search(rb"(\d+)\.(\d+).\d+", output, flags=re.IGNORECASE)
        if match_ is not None:
            version = tuple((int(match_[x]) for x in range(1, 3)))
            if version >= (23, 1):
                return True
    return False

def get_psse_version(path_to_dir: Path):
    readme_file = path_to_dir / 'readme.txt'
    if readme_file.exists():
        try:
            with open(readme_file, 'r') as fp:
                output = fp.read()
                match_ = re.search(r"(\d+)\.(\d+).(\d+)", output, 
                        flags=re.IGNORECASE)
                if match_ is not None:
                    version = tuple((int(match_[x]) for x in range(1, 4)))
                    return version
        except OSError as e:
            # print('OSError', e)
            pass
    return None

def is_valid_psse_version(path_to_dir: Path):
    # read the first line from readme.txt in the toplevel psse_dir to get the
    # version and see if it's greater than or equal to 35.6.2
    
    version = get_psse_version(path_to_dir)
    return version is not None and version >= (35, 6, 2)

def set_file_type_association(exe_path, icon_name, extension):
    exe_path = Path(exe_path).resolve()
    sfta_path = consts.PPD_DIR / "PS-SFTA\\SFTA.ps1"
    ico_path = consts.IMG_DIR / icon_name

    ps_command = f"""Register-FTA '{exe_path}' {extension} -Icon '{ico_path}'"""
    cmd_command = f"""powershell -ExecutionPolicy Bypass -command "& {{ . '{sfta_path}'; {ps_command} }}" """

    # print("Power shell SFTA string:")
    # print(cmd_command)

    p = subprocess.run(
        cmd_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, creationflags=subprocess.CREATE_NO_WINDOW
    )
    logger.info("set FTA results: %s", p.stdout)
    return p.returncode
