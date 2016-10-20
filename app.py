from flask import Flask, abort

from app.request_handler import searchLocation


app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/api/v1.0/at/<string:latitude>/<string:longitude>', methods=['PUT'])
def placeUser(latitude, longitude):
    try:
        latitude, longitude = float(latitude), float(longitude)
        searchLocation(latitude, longitude)
    except ValueError:
        abort(404)
    except KeyboardInterrupt:
        log.info("GOODBYE")
        sys.exit(1)
    except Exception, err:
        from app.util import log
        log.exception("Unknown exception")
        abort(500)
    return "OK - %.4f, %.4f" % (latitude, longitude)

if __name__ == '__main__':
    app.run(debug=True)