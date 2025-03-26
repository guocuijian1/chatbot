from flask import Flask, render_template, request, jsonify
from flask_assets import Environment
from webassets import Bundle

from chatservice import Chat

app = Flask(__name__)
app.config['DEBUG'] = True
# Setup Flask-Assets
assets = Environment(app)

# SCSS Compilation
scss = Bundle('scss/style.scss', output='css/style.css', filters='libsass')
assets.register('scss_all', scss)
scss.build()  # This compiles SCSS into CSS


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():  # put application's code here
    user_message = request.json.get('message')
    response = Chat.chat(user_message, [])
    return jsonify({'response': response})


@app.route('/chat/new_topic', methods=['DELETE'])
def new_topic():  # put application's code here
    response = Chat.new_topic()
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)
