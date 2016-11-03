from flask import Flask, abort

from app.queue.enqueue import searchLocation


app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/api/v1.0/at/<string:latitude>/<string:longitude>', methods=['PUT'])
def placeUser(latitude, longitude):
    try:
        latitude, longitude = float(latitude), float(longitude)
        jobCount = searchLocation(latitude, longitude)
        return "OK %.8f,%.8f / %d" % (latitude, longitude, jobCount)
    except ValueError:
        abort(404)
    except KeyboardInterrupt:
        log.info("GOODBYE")
        sys.exit(1)
    except Exception, err:
        from app.util import log
        log.exception("Unknown exception")
        abort(500)
    

if __name__ == '__main__':
    app.run(debug=True)