import os
import random
from flask import Flask, render_template, jsonify
import openai

app = Flask(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')

drawn_numbers = []


def draw_number():
    remaining = [n for n in range(1, 76) if n not in drawn_numbers]
    if not remaining:
        return None
    prompt = f"Escolha aleatoriamente um numero desta lista: {remaining}. Apenas retorne o numero."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3,
        )
        text = response.choices[0].message['content'].strip()
        number = int(''.join(filter(str.isdigit, text.splitlines()[0])))
    except Exception:
        number = random.choice(remaining)
    drawn_numbers.append(number)
    return number


@app.route('/')
def index():
    return render_template('index.html', numbers=list(range(1, 76)), drawn=drawn_numbers)


@app.route('/draw', methods=['POST'])
def draw():
    number = draw_number()
    return jsonify({'number': number})


@app.route('/reset', methods=['POST'])
def reset():
    drawn_numbers.clear()
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
