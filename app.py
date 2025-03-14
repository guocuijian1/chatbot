from flask import Flask
from chatservice import Chat

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'hello'


@app.route('/chat')
def chat():  # put application's code here
    ins = Chat.get_instance()
    return ins.chat('How many products do you have?', [])


if __name__ == '__main__':
    app.run()
