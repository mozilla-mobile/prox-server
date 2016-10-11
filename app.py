from flask import Flask, abort

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/api/v1.0/at/<string:latitude>/<string:longitude>', methods=['GET'])
def placeUser(latitude, longitude):
    try:
        latitude, longitude = float(latitude), float(longitude)
    except ValueError:
        abort(404)
    return "OK - %.4f, %.4f" % (latitude, longitude)

if __name__ == '__main__':
    app.run(debug=True)