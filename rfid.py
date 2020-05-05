#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import thread
import sys
import json
import time

API_KEY = "3b8cbbcf-b10e-41a9-8cee-a9a956bd9c1f"

def PROCESS_DATA(DATA):
	global client
	if DATA['results'] != []:
		L = len(DATA['results'])
		print DATA['time_now'] 
		with open('./data/transient', 'w+') as f:
			f.write(json.dumps(DATA['results']))	
		for x in range (0,L):
			PRESENCE = DATA['results'][L-x-1]
			try:
				if PRESENCE['location']['label']!="":
					LOCATION_LABEL = PRESENCE['location']['label']
				else:
					LOCATION_LABEL = PRESENCE['location']['id']
				if PRESENCE['item']['label']!="":
					ITEM_LABEL = PRESENCE['item']['code_hex']+"->"+PRESENCE['item']['label']
				else:
					ITEM_LABEL = PRESENCE['item']['code_hex']			
				ITEM_PROXIMITY = PRESENCE['proximity']
				print LOCATION_LABEL+"-"+ITEM_LABEL+"-"+ITEM_PROXIMITY				
			except Exception, e:
				print str(e)
				print "========================="
				print json.dumps(PRESENCE)
				print "========================="
	else:
		print "No tags detected"
			
def GET_PRESENCE(URL):
	URL = URL
	R = requests.get(URL)	
	if R.status_code == 200:
		PROCESS_DATA(json.loads(R.text))
	else: 
		print "Query error"

def on_disconnect(client, userdata, rc):
	global MQTT_CONNECTED
	MQTT_CONNECTED = False
	while not MQTT_CONNECTED:
		client.connect("broker.hivemq.com", 1883, 60)
		time.sleep(5)

def on_connect(client, userdata, flags, rc):
	global MQTT_CONNECTED
	print "MQTT Server Connected!"
	MQTT_CONNECTED = True
	
target = sys.argv[1]
INTERVAL = 2
mode = ""
if target == "-l":
	mode = "LOCATION"
	location = sys.argv[2]
	item = "any"
	U="https://invengoasia.intellifi.nl/api/presences?limit=1000&key="+API_KEY+"&populate=item,location&location="+location
elif target == "-i":
	mode = "ITEM"
	item = sys.argv[2]
	location = "any"
	U="https://invengoasia.intellifi.nl/api/presences?limit=1000&key="+API_KEY+"&populate=item,location&item="+item
elif target == "-il" or target == "-li": 
	mode = "ITEMLOCATION"
	item,location = sys.argv[2].split(",")
	U="https://invengoasia.intellifi.nl/api/presences?limit=1000&key="+API_KEY+"&populate=item,location&item="+item+"&location="+location
print "Scan presence of item: "+item + "@" + location
print "URL: "+U

while 1:
	thread.start_new_thread(GET_PRESENCE,(U,))
	time.sleep(INTERVAL) 
