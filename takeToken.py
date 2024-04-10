import telebot
import config
import random

bot = telebot.TeleBot(config.TOKEN)

def generate_unique_token():
    while True:
        token = random.randint(1, 2)
        if token not in config.existing_tokens:
            config.existing_tokens.add(token)
            return token
