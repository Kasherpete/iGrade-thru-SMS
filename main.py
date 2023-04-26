import pytextnow
import igrade_cmd
import credentials

pytn_client = pytextnow.Client(username=credentials.get_username(), sid_cookie=credentials.get_sid(), csrf_cookie=credentials.get_csrf())
print('Program Start')


@pytn_client.on('message')
def handler(msg):
    msg_content = msg.content.lower()
    print(f"User '{msg.number}' said '{msg_content}'.")

    if msg_content[0] == '!':  # if command

        if msg_content == '!igrade' or msg_content == '!grades':
            igrade_cmd.start(msg)

