import pytextnow
import igrade_cmd
import credentials
import os
from shutil import rmtree

pytn_client = pytextnow.Client(username=credentials.get_username(), sid_cookie=credentials.get_sid(), csrf_cookie=credentials.get_csrf())
print('Program Starting...')

# init file dirs
try:  # if dir exists
    rmtree("files")
except FileNotFoundError:
    pass

os.makedirs("files/download")
os.mkdir("files/finish")
os.mkdir("files/html_parsing")


print('Program Start.')



@pytn_client.on('message')
def handler(msg):
    msg_content = msg.content.lower()
    print(f"User '{msg.number}' said '{msg_content}'.")

    if msg_content[0] == '!':  # if command

        if msg_content == '!igrade' or msg_content == '!grades':
            igrade_cmd.start(msg)

