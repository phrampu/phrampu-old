#!/usr/bin/python3
import threading
import paramiko, base64
import sys
from json import dumps, loads, JSONEncoder, JSONDecoder

from flask import Flask, json, Response
from flask_cors import CORS, cross_origin
from flask import request

import settings as s
import crawler as c
import who
import requests

logger = s.logging.getLogger()
s.getargs(logger)

# clears db if needed
# c.mongologs.drop()

threading.Thread(target=c.spawnThreads, daemon=True).start()

app = Flask(__name__)
CORS(app)

@app.route("/api/master")
@cross_origin()
def api_master():
    js = json.dumps({'response': c.whoCache})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/counts")
@cross_origin()
def api_counts():
    js = json.dumps({'response': who.freeLabCount(c.whoCache)})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/find")
@cross_origin()
def api_lastfound():
    regex = request.args.get('regex', '')
    js = json.dumps({'response': c.find(regex)})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/cluster/<cluster_name>")
@cross_origin()
def api_cluster(cluster_name):
    js = json.dumps({'response': c.whoCache[cluster_name]})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/calendar/<cluster_name>")
@cross_origin()
def api_calendar(cluster_name):
    calendar=s.MACHINES['clusters'][cluster_name]['calendar']
    data = requests.get("https://clients6.google.com/calendar/v3/calendars/{cal}@group.calendar.google.com/events?calendarId={cal}%40group.calendar.google.com&singleEvents=true&timeZone=America%2FNew_York&maxAttendees=1&maxResults=250&sanitizeHtml=true&timeMin=2016-11-13T00%3A00%3A00-05%3A00&timeMax=2016-11-20T00%3A00%3A00-05%3A00&key=AIzaSyBNlYH01_9Hc5S1J9vuFmu2nUqBZJNAXxs".format(cal=calendar))
    js = json.dumps({"response": json.loads(data.content.decode())})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/log")
@cross_origin()
def api_log():
    js = open("server.log").read()
    resp = Response(js, status=200, mimetype='application/json')
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=s.PORT)
