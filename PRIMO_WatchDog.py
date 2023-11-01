# -*- coding: utf-8 -*-

"""

v1.10: no changes. Added gamma criteria defined by user in CONFIG file.
       MH. 1/11/23

v1.09_para_GitHub: no new functionalities. Simplifications to publish in
                   Github. Quiron edition removed. MH. 8/10/23.

v1.09: no changes respect to 1.07. MH. 1/11/22.

v1.08: no changes respect to 1.07. MH. 23/2/22.

v1.07: no changes respect to 1.06. MH. 15/2/22.

v1.06: no changes respect to 1.05. MH. 14/2/22.

v1.05: Changes spaces in filenames to "_". 13/2/22. MH.

v1.04: no changes respect to 1.03. MH.

v1.03: changes # in filenames. Added "# QUIRON", so only one edition of the
       program is needed. 22/1/22. MH.

v1.02: Implementation of recursive watchdog, to allow using DICOM files or
       directly a folder full of DICOM files.

v1.01: Dec 28, 2021


Created on Sun Oct 31 19:59:07 2021

@author: Marce
"""
import glob
import os
import threading
import time
import sys

from automate_PRIMO_simulations import automate_PRIMO_simulation
from colorama import init, Fore, Back, Style
init(strip=not sys.stdout.isatty()) # strip colors if stdout is redirected

from pyfiglet import figlet_format
from termcolor import cprint
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from write_to_log import write_to_log

class Colors: # You may need to change color settings
    RED = '\033[31m'
    ENDC = '\033[m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'

os.system('color')    # to be able to use color text to the console



# VERSION
VERSION = "v. 1.10"

# Create the event handler
# The event handler is the object that will be notified when something
# happen on the filesystem you are monitoring.
if __name__ == "__main__":
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = True
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns,
                        ignore_patterns,ignore_directories, case_sensitive)

    
    # close splash screen
    try:
        import pyi_splash
        pyi_splash.update_text('UI Loaded ...')
        pyi_splash.close()
    except:
        pass
    
        
    #    read CONFIG file
    # Source: (https://stackabuse.com/read-a-file-line-by-line-in-python/)
    #with open('.\\CONFIG.DOG', encoding="UTF-8") as config_file:
    #              config_lines = config_file.readlines()   # read lines of file    
    
    if os.environ['COMPUTERNAME'] == 'LAPTOP-78R8OE0P':
        with open('.\\CONFIG_LAPTOP.DOG', encoding="UTF-8") as config_file:
                  config_lines = config_file.readlines()   # read lines of file
    else:
        with open('.\\CONFIG.DOG', encoding="UTF-8") as config_file:
                  config_lines = config_file.readlines()   # read lines of file                
    
    
        
    for index, line in enumerate(config_lines):
        if line == "# DICOM RT IMPORT FOLDER\n":
                watched_folder = config_lines[index + 1].strip('\n')
        
    #    read CONFIG file
    # Source: (https://stackabuse.com/read-a-file-line-by-line-in-python/)
    if os.environ['COMPUTERNAME'] == 'LAPTOP-78R8OE0P':
        with open('.\\CONFIG_LAPTOP.DOG', encoding="UTF-8") as config_file:
                  config_lines = config_file.readlines()   # read lines of file
    else:
        with open('.\\CONFIG.DOG', encoding="UTF-8") as config_file:
                  config_lines = config_file.readlines()   # read lines of file    

    for index, line in enumerate(config_lines):
        if line == "# DICOM RT IMPORT FOLDER\n":
                watched_folder = config_lines[index + 1].strip('\n')
                        
                
                
    # Presentation
    cprint(figlet_format('PRIMO WatchDog', font='big'),
       'green', attrs=['bold'])

    print(Fore.YELLOW + Back.BLACK + Style.BRIGHT +
          VERSION + ". Marcelino Hermida (2023)")
    
    print("\n" + Fore.GREEN + Style.BRIGHT + "Waiting for DICOM files \n")
    write_to_log("PRIMO WATCHDOG " + VERSION + \
               " is active. Waiting for DICOM files")
    
    
    # functions to be run on specified events 
    def on_created(event):
        print(f"{event.src_path} has been CREATED!")
        #list = os.listdir(watched_folder) # dir is your directory path
        file_list = glob.glob(watched_folder + "/**/*.*", recursive = True)
        number_files = len(file_list)
        print (number_files, "files in the watched folder!")


    def on_deleted(event):
        print(f"{event.src_path} has been DELETED!")
        #list = os.listdir(watched_folder) # dir is your directory path
        file_list = glob.glob(watched_folder + "/**/*.*", recursive = True)
        number_files = len(file_list)
        print (number_files, "files in the watched folder!")


    def on_modified(event):
        print(f"{event.src_path} has been MODIFIED")
        #list = os.listdir(watched_folder) # dir is your directory path
        file_list = glob.glob(watched_folder + "/**/*.*", recursive = True)
        number_files = len(file_list)
        print (number_files, "files in the watched folder!")


    def on_moved(event):
        print(f"{event.src_path} was MOVED to {event.dest_path}")
        #list = os.listdir(watched_folder) # dir is your directory path
        file_list = glob.glob(watched_folder + "/**/*.*", recursive = True)
        number_files = len(file_list)
        print (number_files, "files in the watched folder!")


    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved


    # create an observer
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, watched_folder,
                         recursive=go_recursively)


    # Start the observer
    my_observer.start()
    
    number_files_old = 0
    try:
        while True:
            file_list = glob.glob(watched_folder + "/**/*.*", recursive = True)
            number_files = len(file_list)
            print (Colors.YELLOW + (str(number_files) +\
                   " files in the watched folder: " +\
                   watched_folder) + Colors.ENDC)
            print(Colors.GREEN + ' Waiting for DICOM files \n' + Colors.ENDC)
                
            if (number_files == number_files_old & number_files > 0):
                print(" All DICOM files received! \n")
                write_to_log(str(number_files) + " DICOM files received")
                
                # change # in the filename                
                file_list = glob.glob(watched_folder + "/**/*.*",
                                      recursive = True)

                for filename in file_list:    
                    original_filename = os.path.basename(filename)
                    original_path = os.path.dirname(filename)
                    if '#' in original_filename and '.dcm' in original_filename:
                        # "#" not valid character in PRIMO
                        new_filename = original_filename.replace("#", "_")  
                        os.rename(os.path.join(original_path,original_filename),
                                  os.path.join(original_path, new_filename))
                    
                # change spaces in the filename to "_"                
                file_list = glob.glob(watched_folder + "/**/*.*",
                                      recursive = True)

                for filename in file_list:    
                    original_filename = os.path.basename(filename)
                    original_path = os.path.dirname(filename)
                    if " " in original_filename and '.dcm' in original_filename:
                        new_filename = original_filename.replace(" ", "_")  
                        os.rename(os.path.join(original_path,
                                               original_filename),
                                  os.path.join(original_path, new_filename))
                
                
                
                # Create a Thread with automate_PRIMO_simulation function
                thread = threading.Thread(target=automate_PRIMO_simulation)
                # Start the thread
                thread.start()
                
            number_files_old = number_files
            
            time.sleep(3)      # standard pause of 3 s
    
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()


