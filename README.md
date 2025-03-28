# PSLF PSSE Disambiguator (PPD)
A utility program for running PSLF and PSSE easily on the same computer.
The purpose of the program is to allow left clicking to start a .sav file in
the windows file explorer to automatically determine which model validation
program that the file should be opened in.

## Installation
1. Download the latest release from [here]([url](https://github.com/charlie-peregrine/pslf-psse-disambiguator/releases)).
2. Extract the zip file.
3. Move the extracted folder to where you would like it to stay on your computer. This could be somewhere specific or it can just live in your downloads folder.
4. Open the folder and run pslf-psse-disambiguator.py. Follow the instructions.
5. After clicking "OK" the program will automatically set a file type association, and the program will run whenever you open a .sav file on your program.

You should only have to go into the folder and run pslf-psse-disambiguator.py once per install.
However, you can run the file again to modify your settings.

## Installation problems or bug reports
If you have any problems installing PPD or you run into a bug while using it (characterized by an error window
popping up or some other crash), please contact me at charlie@peregrineengineering.com. If possible,
please include ppd.log in your bug report.

## Usage and features
PPD has 3 sections: A setup window, the disambiguator window, and an update check. 

### Setup
Use setup to select the correct location of pslf and psse. The setup window also contains
information that may make using PPD easier. The setup window will automatically check that
your enterred directories are valid, and all the setup information is saved to a configuration file.

### Disambiguator
The disambiguator window, for the most part, will never actually show up during normal use. It can
be forced to show by pressing the control key when the loading popup appears, or by checking the 'use prompt'
checkbox during setup. Whether or not the actual window is shown, under the hood 3 checks are run to determine
the type of the selected .sav file.

First, the program keeps a history lookup table, and checks that to see if
the selected .sav file has been opened previously. Second, the program checks the leading bytes of the .sav file.
PSLF and PSSE both save their loadflows with distinct leading bytes, so checking them this way is a simple and fast
method for checking. If both of the above fail and the installed PSLF and PSSE versions are both high enough to use
their python APIs, a third check is run where the programs are both run in the background, and whichever one successfully
opens the file is determined to be the correct program.

### Update checker
During every run, the program checks to see if this repository contains an update, and will show a window after the
program runs to allow the user to update. You can also snooze this reminder, and the snooze increment is as many
days as you want.


## Build Requirements
To build from source, you must have the pyinstaller, pywin32, psutil, pillow, and filelock modules installed.
Run `pyinstaller.exe pslf-psse-disambiguator.spec -y` to build. You can also run build.bat instead.
If the build succeeds the files will be in the dist directory.
