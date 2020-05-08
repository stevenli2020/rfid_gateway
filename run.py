#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import json
import time
from datetime import datetime
import signal
import atexit
import traceback
import random
import rfid

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
rfid.POST(PID,POST_FILE,"Job started")
	
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

rfid.GET_PRESENCE(JOBS,JOB_ID,POST_FILE,LOG_FILE)
		
		 	


