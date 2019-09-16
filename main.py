from network import WLAN
import urequests as requests
import machine
import time
import ujson as json
import ufirebase as firebase

DELAY = 5  # Delay in seconds

wlan = WLAN(mode=WLAN.STA)
wlan.antenna(WLAN.INT_ANT)

# Assign your Wi-Fi credentials
wlan.connect("", auth=(WLAN.WPA2, ""), timeout=5000)

while not wlan.isconnected ():
    machine.idle()
print("Connected to Wifi\n")

config = {
  "apiKey": "AIzaSyAT44nTgkuVOCrjIjTvdkH8Id_ydhvFwag",
  "authDomain": "colourfi-66678.firebaseapp.com",
  "databaseURL": "https://colourfi-66678.firebaseio.com",
  "storageBucket": "colourfi-66678.appspot.com"
}

firebase = firebase.initialize_app(config)

email = ""
password = ""

time.sleep(DELAY)

auth = firebase.auth()
db = firebase.database()

user = auth.sign_in_with_email_and_password(email, password)
uid = user['localId']
authToken = user['idToken']
print(uid)

print (db.child('users').child(uid).get(authToken))
