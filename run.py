#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import thread
import sys,os
import json
import time
from datetime import datetime
import signal
import atexit
import traceback
import random
import hashlib

def HANDLE_EXIT(*arg): 
	global JOBS,JOB_ID,EXITING,POST_FILE
	if os.path.isfile(POST_FILE):
		os.remove(POST_FILE)
	if not EXITING:
		EXITING = True
		time.sleep(random.random()/2.0)
		if os.path.isfile('/app/run/jobs.json'):
			with open('/app/run/jobs.json', 'r+') as f0:
				JOBS = json.loads(f0.read())
				JOBS[JOB_ID]['pid'] = 0
				JOBS[JOB_ID]['status'] = "stopped"
				JOBS[JOB_ID]['exited'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
				f0.seek(0)
				f0.write(json.dumps(JOBS))
				f0.truncate()
			with open('/app/jobs.json','r+') as f0:
				f0.seek(0)
				f0.write(json.dumps(JOBS))
				f0.truncate()	
		print "\n"+datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")+" > "+JOB_ID+": Bye!\n"
		sys.exit()
	
atexit.register(HANDLE_EXIT)
signal.signal(signal.SIGTERM, HANDLE_EXIT)
signal.signal(signal.SIGINT, HANDLE_EXIT)

def GET_PRESENCE(MODE,URL,INT):
	global JOB_ID
	# print "Report mode = "+MODE
	# print "URL = "+URL
	while 1:
		try:
			R = requests.get(URL)	
			TIME = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
			if R.status_code != 200:
				print "Status code:" + str(R.status_code)
			else: 
				DATA = json.loads(R.text)
				try:
					L = len(DATA['results'])
					REPORT = {}
					REPORT['time']=TIME
					REPORT['type']=MODE					
					if L > 0:
						# POST(json.dumps(DATA['results']))
						if MODE == "location":
							REPORT['locations']={}
							for x in range (0,L):
								LOCATION = DATA['results'][x]['location']
								ITEM = DATA['results'][x]['item']
								if LOCATION['id'] not in REPORT['locations']:
									REPORT['locations'][LOCATION['id']]={}
								if 'label' not in REPORT['locations'][LOCATION['id']]:
									REPORT['locations'][LOCATION['id']]['label']=LOCATION['label']
								if 'items' not in REPORT['locations'][LOCATION['id']]:
									REPORT['locations'][LOCATION['id']]['items']=[]
								I = {}
								I['id']=ITEM['id']
								I['code_hex']=ITEM['code_hex']
								I['label']=ITEM['label']
								I['sets']=ITEM['sets']
								I['proximity']=DATA['results'][x]['proximity']
								REPORT['locations'][LOCATION['id']]['items'].append(I)
						elif MODE == "item" or MODE == "match":
							REPORT['items']={}
							for x in range (0,L):
								LOCATION = DATA['results'][x]['location']
								ITEM = DATA['results'][x]['item']
								if ITEM['id'] not in REPORT['items']:
									REPORT['items'][ITEM['id']]={}
								if 'label' not in REPORT['items'][ITEM['id']]:
									REPORT['items'][ITEM['id']]['label']=ITEM['label']
								if 'locations' not in REPORT['items'][ITEM['id']]:
									REPORT['items'][ITEM['id']]['locations']=[]	 
								I = {}	
								I['id']=LOCATION['id']
								I['label']=LOCATION['label']
								I['position']=LOCATION['custom']['position']
								I['proximity']=DATA['results'][x]['proximity']
								REPORT['items'][ITEM['id']]['locations'].append(I)
					print json.dumps(REPORT)+"\n"
					POST(json.dumps(REPORT))
				except Exception as e:
					ERROR = str(e)+"\n"+str(sys.exc_info()[2])
					LOG(ERROR)
					pass
		except Exception as e:
			ERROR = str(e)+"\n"+str(sys.exc_info()[2])
			LOG(ERROR)
			time.sleep(5)
			continue			
		time.sleep(INT)

def POST(MESSAGE):
	global POST_FILE,PID
	DATA = "PID="+str(PID)+"\n"+datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")+"\r\n"+str(MESSAGE)
	with open(POST_FILE, 'w+') as f:
		f.write(DATA)	

def LOG(MESSAGE):
	global LOG_FILE
	DATA = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")+"\r\n"+str(MESSAGE)+"\r\n"
	with open(LOG_FILE, 'a+') as f:
		f.write(DATA)	
		
def UNHANDLED_EXCEPTION(exctype, value, tb):
	global LOG_FILE
	MESSAGE = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")+"\r\n<UNHANDLED_EXCEPTION>\n"
	MESSAGE = MESSAGE + "TYPE:" + str(exctype) + "\n"
	MESSAGE = MESSAGE + "VALUE:\n" + str(value) + "\n"
	MESSAGE = MESSAGE + "TRACE BACK:\n" + str(tb) + "\n"
	with open(LOG_FILE, 'a+') as f:
		f.write(MESSAGE)
		
sys.excepthook = UNHANDLED_EXCEPTION		
#===================================================================
EXITING = False 
JOB_ID = sys.argv[1]
POST_FILE = '/app/run/'+JOB_ID
LOG_FILE = '/app/run/LOG-'+JOB_ID
PID = os.getpid()
POST("Job started")
	
with open('/app/jobs.json', 'r+') as f0:
	JOBS = json.loads(f0.read())
	JOBS[JOB_ID]['pid'] = PID
	JOBS[JOB_ID]['status'] = "started"
	JOBS[JOB_ID]['started'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
	if 'config' in JOBS[JOB_ID]:
		if JOBS[JOB_ID]['config']=="":
			with open("default-config.json", 'r') as f1:
				CONFIG = json.loads(f1.read())		
			JOBS[JOB_ID]['config']=CONFIG
	else:
		with open("default-config.json", 'r') as f1:
			CONFIG = json.loads(f1.read())	
		JOBS[JOB_ID]['config']=CONFIG
	f0.seek(0)
	f0.write(json.dumps(JOBS))
	f0.truncate()
# sys.exit()
R = requests.get("http://localhost:8080/DeviceId")

while R.status_code != 200:
	print "Status code:" + str(R.status_code)
	time.sleep(2)
	print "Retry ..."
	R = requests.get("http://localhost:8080/DeviceId")
DEVICE_ID = json.loads(R.text)['DeviceId']
# print "DEVICE_ID = "+DEVICE_ID
SERVICE_KEY = hashlib.sha1(hashlib.sha512(DEVICE_ID).hexdigest()+hashlib.sha512("AVNET").hexdigest()).hexdigest()
# print "SERVICE_KEY = "+SERVICE_KEY
if SERVICE_KEY != JOBS[JOB_ID]['config']['service_key']:
	print "Service key error"
	sys.exit()

QUERYSTRING = ""
if 'items' in JOBS[JOB_ID]:
	for item in JOBS[JOB_ID]['items']:
		QUERYSTRING = QUERYSTRING + "&item=" + item
if 'locations' in JOBS[JOB_ID]:		
	for location in JOBS[JOB_ID]['locations']:
		QUERYSTRING = QUERYSTRING + "&location=" + location
print "Start job now"
print QUERYSTRING

thread.start_new_thread(GET_PRESENCE,(JOBS[JOB_ID]['mode'],"https://"+JOBS[JOB_ID]['config']['brain_address']+"/api/presences?limit=1000&key="+JOBS[JOB_ID]['config']['api_key']+"&populate=item,location"+QUERYSTRING,JOBS[JOB_ID]['config']['report_interval']))

while 1:
	time.sleep(10)

		
		 	


