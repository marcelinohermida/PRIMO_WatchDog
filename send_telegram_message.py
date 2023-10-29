# -*- coding: utf-8 -*-
"""
Created on Wed Nov  3 00:06:04 2021

@author: Marce

Based on 
https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-messages-with-python-4cf314d9fa3e

"""



def telegram_bot_sendtext(bot_message, bot_token, bot_chatID):

    import requests
    # bot_token = '638395733:AAEZ24otsI8dSA8XvAXYnkGKW3hFpBYzHsQ'
    # bot_chatID = '7664629'
    send_text = ('https://api.telegram.org/bot' + bot_token +
        '/sendMessage?chat_id=' + bot_chatID +
        '&parse_mode=Markdown&text=' + bot_message)

    # Send Trump gif (only for JFC!)
#    send_trump = ("https://api.telegram.org/bot" + bot_token +
#                  "/sendVideo?chat_id=" + bot_chatID +
#                  "&video=" + "https://c.tenor.com/5h-E8J9rnowAAAAM/donald-trump-dancing.gif")
#    

    response = requests.get(send_text)
    #response = requests.get(send_trump)

    return response.json()
  
    




#bot_token = '638395733:AAEZ24otsI8dSA8XvAXYnkGKW3hFpBYzHsQ'
#bot_chatID = '7664629'
def telegram_bot_senddocument(simulation_folder, document, caption,
                              bot_token, bot_chatID):
    import requests
    import os    

    os.chdir(simulation_folder)
    response = requests.post('https://api.telegram.org/bot' +
                             bot_token + '/sendDocument',
                             files={'document': (document,
                                                 open(document, 'rb'))},
                             data={'chat_id': bot_chatID, 'caption': caption})

    return response.json()




#, 'caption': ' sdfsdfsd'