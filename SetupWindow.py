# SetupWindow.py, Charlie Jordan, 3/10/2025

import importlib.util
import re

import subprocess
import sys
from typing import Callable
from pathlib import Path
from PIL import Image, ImageTk
from PIL.Image import Resampling


import tkinter as tk
from tkinter import ttk

import consts
import files


class SetupWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("PSLF/PSSE Disambiguator Setup")
        # self.wm_protocol
        
        self.iconphoto(True, tk.PhotoImage(file="./ppd.png"))
        # self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        ### labelframe for setting directories
        self.exe_frame = ttk.Labelframe(self, text="Step 1: Program Directories")
        self.exe_frame.grid(row=0, column=0, sticky='ew')
        self.exe_frame.columnconfigure(1, weight=1)

        icon_size = (16, 16)
        # pslf line with icon, entry, select button
        image = Image.open("./pslf.png").resize(icon_size, Resampling.BICUBIC)
        self.pslf_icon = ImageTk.PhotoImage(image)
        self.pslf_icon_label = ttk.Label(self.exe_frame, compound='left', text='PSLF:', image=self.pslf_icon)
        self.pslf_icon_label.grid(row=1, column=0)
        
        # def pslf_validate(text):
            
        
        self.pslf_entry = ttk.Entry(self.exe_frame, validate='all', width=45)
        self.pslf_entry.insert(0, '')
        self.pslf_entry.grid(row=1, column=1, sticky='ew')
        self.pslf_select_button = ttk.Button(self.exe_frame, text="Select")
        self.pslf_select_button.grid(row=1, column=2)
        
        # psse line with icon, entry, select button
        image = Image.open("./psse.png").resize(icon_size, Resampling.BICUBIC)
        self.psse_icon = ImageTk.PhotoImage(image)
        self.psse_icon_label = ttk.Label(self.exe_frame, compound='left', text='PSSE:', image=self.psse_icon)
        self.psse_icon_label.grid(row=2, column=0)

        self.psse_entry = ttk.Entry(self.exe_frame, validate='all', width=45)
        self.psse_entry.insert(0, '')
        self.psse_entry.grid(row=2, column=1, sticky='ew')
        self.psse_select_button = ttk.Button(self.exe_frame, text="Select")
        self.psse_select_button.grid(row=2, column=2)

        ### Labelframe for misc options
        self.misc_frame = ttk.LabelFrame(self, text="Step 2: Preferences and Hints")
        self.misc_frame.grid(row=1, column=0, sticky='ew')
        self.misc_frame.columnconfigure(1, weight=1)

        # skip prompt checkbox
        self.skip_prompt_checkbox = ttk.Checkbutton(self.misc_frame)
        self.skip_prompt_checkbox.grid(row=0, column=0)
        self.skip_prompt_label = ttk.Label(self.misc_frame, wraplength=450,
                text="Show a prompt to pick which program to run for a sav file regardless of the automatically detected type. If unsure, it is recommended to leave this box unchecked.",
                justify='left')
        self.skip_prompt_label.grid(row=0, column=1)
        # hint about hold control to show window regardless of skip prompt
        self.hint_label = ttk.Label(self.misc_frame, wraplength=400,
                text="HINT: If you left the box above unchecked you can still access the prompt by holding Control while opening a sav file.",
                justify='left')
        self.hint_label.grid(row=1, column=0, columnspan=2)
        # Status for using python libraries
        # @TODO add textvariable and variable depending on results
        self.py_library_checkbox = ttk.Checkbutton(self.misc_frame)
        self.py_library_checkbox.grid(row=2, column=0)
        self.py_library_label = ttk.Label(self.misc_frame, text="Python Library Status", justify='left')
        self.py_library_label.grid(row=2, column=1)
        
        ### History Labelframe
        # self.history_frame = ttk.Labelframe(self, text="Step 3: History")
        # self.history_frame.grid(row=0, column=1, rowspan=2)
        
        
        # clear history, remove from history, edit history? 
        
        # buttons to save and close
        ### Button Frame
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=4, column=0, sticky='ew')
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        sep = ttk.Separator(self.button_frame, orient='horizontal')
        sep.grid(row=0, column=0, columnspan=2, sticky='ew')
        
        self.ok_button = ttk.Button(self.button_frame, text="OK")
        self.ok_button.grid(row=2, column=0, sticky='ew')
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel")
        self.cancel_button.grid(row=2, column=1, sticky='ew')

        
        for frame in (self.exe_frame, self.misc_frame, self.button_frame):
            for widget in frame.winfo_children():
                widget.grid_configure(padx=4, pady=3)



# class WrapLabel(ttk.Label):
#     def __init__(self, parent, *args, **kwargs):
#         super().__init__(parent, *args, **kwargs)
        
#         self.bind("<Configure>", self.change_wrap)
    
#     def change_wrap(self, e):
#         print(self.grid_bbox())


def is_valid_pslf_version(path_to_exe: Path):
    # use 'Pslf.exe --version' and checkoutput to see if version is greater than or equal to 23.1.0
    if path_to_exe.exists():
        p = subprocess.run(f'"{path_to_exe}" --version', stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT)
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
        except OSError:
            pass
    return None

def is_valid_psse_version(path_to_dir: Path):
    # read the first line from readme.txt in the toplevel psse_dir to get the
    # version and see if it's greater than or equal to 35.6.2
    
    version = get_psse_version(path_to_dir)
    return version is not None and version >= (35, 6, 2)

def keep_asking(
    prompt: str = "(y/n) ",
    yes_test: str | Callable[[str], bool] = 'y',
    no_test: str | Callable[[str], bool] = 'n',
    yes_print: str | None = None,
    no_print: str | None = None,
    reprompt: str = "Enter y or n for yes or no"
):
    if isinstance(yes_test, str):
        yes_test_ = lambda x: x == yes_test
    else:
        yes_test_ = yes_test
    if isinstance(no_test, str):
        no_test_ = lambda x: x == no_test
    else:
        no_test_ = no_test
    while True:
        inp = input(prompt)
        if yes_test_(inp):
            if yes_print is not None:
                print(yes_print)
            return True
        elif no_test_(inp):
            if no_print is not None:
                print(no_print)
            return False
        else:
            print(reprompt)

def setup_():
    configs = files.load_config()
    if configs is None:
        pslf_dir_path = consts.DEFAULT_PSLF_DIR_PATH
        psse_dir_path = consts.DEFAULT_PSSE_DIR_PATH
        configs = {}
    else:
        pslf_dir_path = Path(configs['pslf'])
        psse_dir_path = Path(configs['psse'])
        

    print("Using the following directories to find pslf and psse executables.")
    print("If you have multiple versions of either program or installed them")
    print("somewhere different than the default location, you may need to change")
    print("these.")
    print("PSLF:", pslf_dir_path)
    print("PSSE:", psse_dir_path)
    keep_asking("Change these values? (y/n) ", yes_print="edit here (WIP)",
                no_print="Keeping")
    
    
    
    # @TODO check that the exe files exist
    pslf_exe_path = pslf_dir_path / consts.PSLF_EXE_SUFFIX
    if not pslf_exe_path.exists():
        print("pslf.exe not found")
        pass # ask for new directory

    psse_version = get_psse_version(psse_dir_path)
    if psse_version is not None:
        configs['psse_version'] = psse_version
        files.set_psse_version(psse_version[0])
    psse_exe_path = psse_dir_path / consts.PSSE_EXE_SUFFIX
    if not psse_exe_path.exists():
        print(f"{psse_exe_path.name} not found")
        pass # ask for new directory
    
    configs['pslf'] = str(pslf_dir_path)
    configs['psse'] = str(psse_dir_path)
    
    
    print("Skip the 'Pick a program' window when opening a sav file that has")
    print("been opened before? If you're not sure, then choose yes.")
    configs['skip_prompt'] = keep_asking(yes_print="always", no_print="only sometimes")

    pslf_py_path = pslf_dir_path / consts.PSLF_PY_SUFFIX
    psse_py_path = psse_dir_path / consts.PSSE_PY_SUFFIX
    
    # add paths to import search paths
    sys.path.append(str(pslf_py_path.parent))
    sys.path.append(str(psse_py_path.parent))
    
    use_python_libraries = True
    if sys.version_info[:2] != (3, 11):
        use_python_libraries = False
        print("invalid python version to use python libraries")
    else:
        if not is_valid_pslf_version(pslf_exe_path):
            use_python_libraries = False
            print("invalid pslf version for python libraries")
        elif importlib.util.find_spec('PSLF_PYTHON') is None:
            use_python_libraries = False
            print("Can't find pslf python")
        if not is_valid_psse_version(psse_dir_path):
            use_python_libraries = False
            print("invalid psse version for python libraries")
        elif importlib.util.find_spec('psse35') is None:
            use_python_libraries = False
            print("Can't find psse python")
    configs['use_python'] = use_python_libraries
    
    
    files.save_config(configs)
    if not files.load_history():
        files.save_history({})
    
    
    # set fta here
    if consts.IS_BUNDLED:
        pass 
        set_file_type_association(sys.executable, "ppd.ico", ".sav")
    else:
        print("> skipping set fta for unbundled files")

def set_file_type_association(exe_path, icon_name, extension):
    exe_path = Path(exe_path).resolve()
    sfta_path = consts.PPD_DIR / "PS-SFTA\\SFTA.ps1"
    ico_path = consts.PPD_DIR / icon_name

    ps_command = f"""Register-FTA '{exe_path}' {extension} -Icon '{ico_path}'"""
    cmd_command = f"""powershell -ExecutionPolicy Bypass -command "& {{ . '{sfta_path}'; {ps_command} }}" """

    # print("Power shell SFTA string:")
    # print(cmd_command)

    p = subprocess.run(
        cmd_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    print(p.stdout)
    return p.returncode
