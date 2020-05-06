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
import random


def HANDLE_EXIT(*arg): 
	global JOBS,JOB_ID
	time.sleep(random.random())
	with open('/app/data/jobs.json', 'r+') as f0:
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
	sys.exit()
	
atexit.register(HANDLE_EXIT)
signal.signal(signal.SIGTERM, HANDLE_EXIT)
signal.signal(signal.SIGINT, HANDLE_EXIT)

def GET_PRESENCE(MODE,ID,URL,INT):
	while 1:
		try:
			R = requests.get(URL)	
		except:
			time.sleep(5)
			continue
		TIME = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
		if R.status_code != 200:
			print "Status code:" + str(R.status_code)
		else: 
			DATA = json.loads(R.text)
			try:
				if DATA['count'] > 0:
					L = len(DATA['results'])
					with open('/app/data/transient', 'w+') as f:
						f.write(json.dumps(DATA['results']))
					REPORT = {}
					REPORT['time']=TIME
					REPORT[ID]={}
					REPORT[ID]['type']=MODE
					if MODE == "location":
						REPORT[ID]['items']=[]
						if DATA['results'][0]['location']['label'] != "":
							REPORT[ID]['label'] = DATA['results'][0]['location']['label']	
						else:
							REPORT[ID]['label'] = ""
						for x in range (0,DATA['count']):
							PRESENCE = DATA['results'][DATA['count']-x-1]
							ITEM = {}
							ITEM['id'] = PRESENCE['item']['id']
							ITEM['code'] = PRESENCE['item']['code_hex']
							ITEM['proximity'] = PRESENCE['proximity']
							ITEM['technology'] = PRESENCE['technology']
							if PRESENCE['item']['label']!="":
								ITEM['label'] = PRESENCE['item']['label']
							else:
								ITEM['label'] =	""		
							REPORT[ID]['items'].append(ITEM)
					elif MODE == "item" or MODE == "match":
						REPORT[ID]['locations']=[]
						if DATA['results'][0]['item']['label'] != "":
							REPORT[ID]['label'] = DATA['results'][0]['item']['label']	
						else:
							REPORT[ID]['label'] = ""
						REPORT[ID]['proximity'] = DATA['results'][0]['proximity']
						REPORT[ID]['technology'] = DATA['results'][0]['technology']
						for x in range (0,DATA['count']):
							PRESENCE = DATA['results'][DATA['count']-x-1]
							ITEM = {}
							ITEM['id'] = PRESENCE['location']['id']
							ITEM['position'] = PRESENCE['location']['custom']['position']
							if PRESENCE['location']['label']!="":
								ITEM['label'] = PRESENCE['location']['label']
							else:
								ITEM['label'] =	""		
							REPORT[ID]['locations'].append(ITEM)	
					print json.dumps(REPORT)+"\n"
				else:
					print "{}\n"
			except:
				pass
		time.sleep(INT)
		
#===================================================================
JOB_ID = sys.argv[1]
PID = os.getpid()
with open('/app/data/jobs.json', 'r+') as f0:
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
URLs = []	
if JOBS[JOB_ID]['mode'] == "location":
	for location in JOBS[JOB_ID]['locations']:
		thread.start_new_thread(GET_PRESENCE,(JOBS[JOB_ID]['mode'],location,"https://"+JOBS[JOB_ID]['config']['brain_address']+"/api/presences?limit=1000&key="+JOBS[JOB_ID]['config']['api_key']+"&populate=item,location&location="+location,JOBS[JOB_ID]['config']['report_interval']))
elif JOBS[JOB_ID]['mode'] == "item":
	for item in JOBS[JOB_ID]['items']:
		thread.start_new_thread(GET_PRESENCE,(JOBS[JOB_ID]['mode'],item,"https://"+JOBS[JOB_ID]['config']['brain_address']+"/api/presences?limit=1000&key="+JOBS[JOB_ID]['config']['api_key']+"&populate=item,location&item="+item,JOBS[JOB_ID]['config']['report_interval']))
elif JOBS[JOB_ID]['mode'] == "match":
	thread.start_new_thread(GET_PRESENCE,(JOBS[JOB_ID]['mode'],JOBS[JOB_ID]['item'],"https://"+JOBS[JOB_ID]['config']['brain_address']+"/api/presences?limit=1000&key="+JOBS[JOB_ID]['config']['api_key']+"&populate=item,location&item="+JOBS[JOB_ID]['item']+"&location="+JOBS[JOB_ID]['location'],JOBS[JOB_ID]['config']['report_interval']))
while 1:
	time.sleep(10)

		
		 	


