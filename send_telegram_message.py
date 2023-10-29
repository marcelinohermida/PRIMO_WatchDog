# -*- coding: utf-8 -*-
"""
Created on Wed Nov  3 00:06:04 2021

@author: Marce

Based on 
https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-
messages-with-python-4cf314d9fa3e

"""

import requests

def telegram_bot_sendtext(bot_message, bot_token, bot_chatID):
    """
    Send a text message to a Telegram bot.

    :param bot_message: The message to send.
    :param bot_token: The Telegram bot token.
    :param bot_chatID: The chat ID of the recipient.
    :return: The JSON response from the Telegram API.
    """
    
    send_text = ('https://api.telegram.org/bot' + bot_token +
        '/sendMessage?chat_id=' + bot_chatID +
        '&parse_mode=Markdown&text=' + bot_message)

    response = requests.get(send_text)
    return response.json()
  
    

def telegram_bot_senddocument(simulation_folder, document, caption,
                              bot_token, bot_chatID):
    """
    Send a document (file) to a Telegram bot.

    :param simulation_folder: The folder containing the document.
    :param document: The document (file) to send.
    :param caption: The caption for the document.
    :param bot_token: The Telegram bot token.
    :param bot_chatID: The chat ID of the recipient.
    :return: The JSON response from the Telegram API.
    """
    
    import os    
    os.chdir(simulation_folder)
    response = requests.post('https://api.telegram.org/bot' +
                             bot_token + '/sendDocument',
                             files={'document': (document,
                                                 open(document, 'rb'))},
                             data={'chat_id': bot_chatID, 'caption': caption})

    return response.json()
