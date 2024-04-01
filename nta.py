from flask import Flask, render_template, request, session, jsonify
import urllib.request
from pusher import Pusher
from datetime import datetime
import httpagentparser
import json
import os
import hashlib
from database import create_connection, create_session, update_or_create_page, select_all_sessions, select_all_user_visits, select_all_pages
app = Flask(__name__)
app.secret_key = os.urandom(24)
# configure pusher object
pusher = Pusher(
    app_id = "1699501",
    key = "21555218907dfeb62da1",
    secret = "286aa070c389c8c16c9f",
    cluster = "ap2")
database = "./pythonsqlite.db"
conn = create_connection(database)
c = conn.cursor()
 
userOS = None
userIP = None
userCity = None
userBrowser = None
userCountry = None
userContinent = None
sessionID = None
def main():
    global conn, c
def parseVisitor(data):
    update_or_create_page(c, data)
    pusher.trigger(u'pageview', u'new', {
        u'page': data[0],
        u'session': sessionID,
        u'ip': userIP
    })
    pusher.trigger(u'numbers', u'update', {
        u'page': data[0],
        u'session': sessionID,
        u'ip': userIP
    })
@app.before_request
def getAnalyticsData():
    global userOS, userBrowser, userIP, userContinent, userCity, userCountry, sessionID
    userInfo = httpagentparser.detect(request.headers.get('User-Agent'))
    userOS = userInfo['platform']['name']
    userBrowser = userInfo['browser']['name']
    userIP = '2405:201:e04c:d8a6:d7a4:f5bd:92c1:c80d' if request.remote_addr == '127.0.0.1' else request.remote_addr
    api = "https://www.iplocate.io/api/lookup/" + userIP
    try:
        resp = urllib.request.urlopen(api)
        result = resp.read()
        result = json.loads(result.decode("utf-8"))
        userCountry = result["country"]
        userContinent = result["continent"]
        userCity = result["city"]
    except:
        print("Could not find: ", userIP)
    getSession()
def getSession():
    global sessionID
    time = datetime.now().replace(microsecond=0)
    if 'user' not in session:
        lines = (str(time)+userIP).encode('utf-8')
        session['user'] = hashlib.md5(lines).hexdigest()
        sessionID = session['user']
        pusher.trigger(u'session', u'new', {
            u'ip': userIP,
            u'continent': userContinent,
            u'country': userCountry,
            u'city': userCity,
            u'os': userOS,
            u'browser': userBrowser,
            u'session': sessionID,
            u'time': str(time),
        })
        data = [userIP, userContinent, userCountry,
                userCity, userOS, userBrowser, sessionID, time]
        create_session(c, data)
    else:
        sessionID = session['user']
@app.route('/')
def index():
    data = ['home', sessionID, str(datetime.now().replace(microsecond=0))]
    parseVisitor(data)
    return f'User data: {data}'
@app.route('/get-all-sessions')
def get_all_sessions():
    data = []
    dbRows = select_all_sessions(c)
    for row in dbRows:
        data.append({
            'ip': row['ip'],
            'continent': row['continent'],
            'country': row['country'],
            'city': row['city'],
            'os': row['os'],
            'browser': row['browser'],
            'session': row['session'],
            'time': row['created_at']
        })
    return jsonify(data)
 
 
if __name__ == '__main__':
    main()
    app.run(debug=True)