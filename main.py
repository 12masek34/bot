import json
import re
import requests
from flask import Flask
from flask.views import MethodView
from flask import request
import os
# from dotenv import load_dotenv
#
# load_dotenv()

app = Flask(__name__)
TOKEN = os.environ.get('TOKEN')
API_URL = os.environ.get('API_URL')
TELEGRAM_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'


# @app.route('/', methods=['POST', 'GET'])
# def index():
#     if request.method == 'POST':
#         rsp = request.get_json()
#         print(rsp)
#         return f'<h1>Hi bot {rsp} <H1/>'
#     return '<h1>Hi bot<H1/>'

def get_data_from_api(command='blogs/'):
    url = API_URL + command
    session = requests.Session()
    try:
        r = session.get(url).json()
    except ValueError:
        r = None
    return r


def get_keyboard(rsp=None):
    try:
        if rsp is not None:
            keyboard = {'inline_keyboard': [[]]}
            for item in rsp:
                keyboard['inline_keyboard'][0].extend(
                    [{'text': str(item['id']) + ' ' + item['title'], 'callback_data': ritem['id']}])
            keyboard = json.dumps(keyboard)
            return keyboard
        elif rsp is None:
            rsp = get_data_from_api()
            keyboard = (
                {'inline_keyboard': [[]]})
            for r in rsp:
                keyboard['inline_keyboard'][0].extend([{'text': str(r['id']) + ' ' + r['title'], 'callback_data': r['id']}])
            keyboard = json.dumps(keyboard)
            return keyboard
        else:
            return None
    except TypeError:
        return None


def get_all_title(rsp):
    r = ''
    for i in rsp:
        r += ''.join(str(i['id']) + ' - ')
        r += ''.join(i['title'] + '\n')

    return r


def send_message_all(chat_id, rsp=None):
    text = get_all_title(rsp)
    session = requests.Session()
    keyboard = get_keyboard(rsp)
    r = session.get(TELEGRAM_URL,
                    params=dict(chat_id=chat_id, text=text, parse_mode='Markdown', reply_markup=keyboard))
    return r.json()


def send_message(chat_id, message, rsp=None):
    keyboard = get_keyboard(rsp)
    session = requests.Session()
    r = session.get(TELEGRAM_URL, params=dict(chat_id=chat_id,
                                              text=message,
                                              parse_mode='Markdown',
                                              reply_markup=keyboard))
    return r.json()


def parse_text(text_message):
    '''/start, /help, /go '''
    addresses = {
        'start': 'blogs/',
    }
    command_pattern_word = r'/\w+'
    message = 'Неверный запрос'
    if '/' in text_message:
        if '/start' in text_message or '/help' in text_message:
            message = 'Меня зовут Дмитрий Мартысь. Этот бот расскажет обо мне.'
            return message
        elif text_message.replace('/', '').isdigit():
            command = text_message.replace('/', '')
            addresses = {f'{command}': f'blogs/{command}'}
            command = addresses.get(command, None)
            return [command] if command else None
        else:
            command = re.search(command_pattern_word, text_message).group().replace('/', '')
            command = addresses.get(command, None)
            return [command] if command else None
    else:
        return message


class BotAPI(MethodView):

    def get(self):
        return '<h1>Hi bot class <H1/>'

    def post(self):

        rsp = request.get_json()
        try:
            text_message = rsp['message']['text']
            chat_id = rsp['message']['chat']['id']
            temporary_message = parse_text(text_message)
            text = 'Неверный запрос.'
            if temporary_message:
                if len(temporary_message) > 10:
                    send_message(chat_id, temporary_message)
                if temporary_message == ['blogs/']:
                    rsp = get_data_from_api(temporary_message[0])
                    if rsp:
                        if temporary_message[0] == 'blogs/':
                            send_message_all(chat_id, rsp)
                else:
                    rsp = get_data_from_api(temporary_message[0])
                    if rsp:
                        send_message(chat_id, message, rsp)
            else:
                send_message(chat_id, text)
        except KeyError:
            if rsp['callback_query']:
                chat_id = rsp['callback_query']['message']['chat']['id']
                detail_url = 'blogs/' + rsp['callback_query']['data']
                data = get_data_from_api(detail_url)['title'] + '\n' + '\n' + get_data_from_api(detail_url)['text']
                send_message(chat_id, data)
            return f'<h1>{rsp}<H1/>'
        return f'<h1>{rsp}<H1/>'


app.add_url_rule(f'/{TOKEN}/', view_func=BotAPI.as_view('bot'))

if __name__ == '__main__':
    app.run()
    # app.run(port=5000, debug=True, use_reloader=True)
