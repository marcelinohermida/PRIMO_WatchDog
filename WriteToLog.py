# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 12:29:00 2021

@author: Marce
"""

def WriteToLog(msg):
    
    from datetime import datetime
    
    # datetime object containing current date and time
    now = datetime.now()
    # dd/mm/YY H:M:S
    date_string = now.strftime("%Y/%m/%d %H:%M:%S")

    with open('.\\PRIMO_watchdog.log', 'a') as log_file:
        msg = date_string + ' ' + msg + '\n'
        log_file.write(msg)





