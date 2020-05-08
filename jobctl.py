#!/usr/bin/env python

from bottle import get, put, run, request, response, error, HTTP_CODES
import json
import os
import socket
import subprocess
import sys
from shutil import copyfile
from subprocess import call
from time import sleep
import time, threading
from datetime import datetime
import thread
import random,string
import atexit,signal
import requests

def HANDLE_EXIT(*arg): 
	global JOBS
	init_jobs()
	with open('/app/jobs.json', 'r+') as f0:
		f0.seek(0)
		f0.write(json.dumps(JOBS))
		f0.truncate()	
	sys.exit()
	
atexit.register(HANDLE_EXIT)
signal.signal(signal.SIGTERM, HANDLE_EXIT)
signal.signal(signal.SIGINT, HANDLE_EXIT)

def app_json(func):
    def inner(*args, **kwargs):
        response.content_type = 'application/json'
        # return json.dumps(func(*args, **kwargs), sort_keys=True, indent=4) + '\n'
        return json.dumps(func(*args, **kwargs))
    return inner

def update_jobs():
	global JOBS
	while 1:
		print datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")+" > Saving jobs.json"
		init_jobs()
		with open('/app/jobs.json', 'r+') as f0:
			f0.seek(0)
			f0.write(json.dumps(JOBS))
			f0.truncate()
		time.sleep(10)
	
def init_jobs():
	global JOBS
	with open('/app/data/jobs.json', 'r+') as f0:
		JOBS=json.loads(f0.read())
	return

def check_pid(pid):        
    try:
        os.kill(pid, 0) 
    except OSError:
        return False
    else:
        return True

def kill_job(ID):
	os.system("pkill -f "+ID)

def kill_job_2(ID):
	subprocess.check_output(['pkill','-f',ID])

def run_job(ID):
	# os.system("nohup /app/run.py "+ID+" >/dev/null 2>&1 &")
	subprocess.Popen(['/app/run.py '+ID], shell=True)
	
@get('/jobs/get/<j>')
def get_jobs(j):
	global JOBS
	init_jobs()
	if j=="all":
		return json.dumps(JOBS)+"\n"
	elif j=="active":
		RESP = []
		for ID,JOB in JOBS.iteritems():
			if JOB['status']=="stopped" or JOB['pid']==0:
				continue
			RESP.append({'id':ID,'name':JOB['name'],'pid':JOB['pid']}) 
		return json.dumps(RESP)+"\n"
	elif j=="inactive":
		RESP = []
		for ID,JOB in JOBS.iteritems():
			if JOB['status']=="stopped" or JOB['pid']==0:
				RESP.append({'id':ID,'name':JOB['name'],'pid':JOB['pid']}) 
		return json.dumps(RESP)+"\n"	
	else:
		return "[]\n"

@get('/jobs/start/<id>')
def start_job(id):
	global JOBS
	init_jobs()
	if id=="all":
		RESP = []
		for ID in JOBS.keys():
			if JOBS[ID]['status'] != "started":
				run_job(ID)
				time.sleep(0.2)
				RESP.append(ID)
		return json.dumps(RESP)+"\n"
	else:
		if JOBS[id]['status'] != "started":
			run_job(id)
			time.sleep(0.2)
			return id+"\n"	
		else:
			return id+" already loaded\n"		
		
@get('/jobs/stop/<id>')
def stop_job(id):
	global JOBS
	init_jobs()
	if id=="all":
		RESP = []
		for ID in JOBS.keys():
			if JOBS[ID]['status'] == "started":
				kill_job_2(ID)
				RESP.append(ID)
		return json.dumps(RESP)+"\n"
	elif id not in JOBS:
		return "\n"
	else:
		kill_job_2(id)
		init_jobs()
		return id+"\n"		

@get('/jobs/disable/<id>')
def disable_job(id):
	global JOBS
	init_jobs()
	if id=="all":
		RESP = []
		for ID in JOBS.keys():
			if JOBS[ID]['status'] == "started":
				kill_job_2(ID)
				time.sleep(0.5)
			if JOBS[ID]['restart'] == "always":
				with open('/app/data/jobs.json', 'r+') as f0:
					JOBS1=json.loads(f0.read())
					JOBS1[ID]['restart']="no"
					f0.seek(0)
					f0.write(json.dumps(JOBS1))
					f0.truncate()				
					RESP.append(ID)
		return json.dumps(RESP)+"\n"
	else:
		if JOBS[id]['status'] == "started":
			kill_job_2(id)
			time.sleep(0.5)
		if JOBS[id]['restart'] == "always":
			with open('/app/data/jobs.json', 'r+') as f0:
				JOBS1=json.loads(f0.read())
				JOBS1[id]['restart']="no"
				f0.seek(0)
				f0.write(json.dumps(JOBS1))
				f0.truncate()
			return id+"\n"	
		else:
			return id+" already disabled\n"

@get('/jobs/enable/<id>')
def enable_job(id):
	global JOBS
	init_jobs()
	if id=="all":
		RESP = []
		for ID in JOBS.keys():
			if JOBS[ID]['status'] != "started":
				run_job(ID)
				time.sleep(0.5)
			if JOBS[ID]['restart'] != "always":
				with open('/app/data/jobs.json', 'r+') as f0:
					JOBS1=json.loads(f0.read())
					JOBS1[ID]['restart']="always"
					f0.seek(0)
					f0.write(json.dumps(JOBS1))
					f0.truncate()				
					RESP.append(ID)
		return json.dumps(RESP)+"\n"
	else:
		if JOBS[id]['status'] != "started":
			run_job(id)
			time.sleep(0.5)
		if JOBS[id]['restart'] != "always":
			with open('/app/data/jobs.json', 'r+') as f0:
				JOBS1=json.loads(f0.read())
				JOBS1[id]['restart']="always"
				f0.seek(0)
				f0.write(json.dumps(JOBS1))
				f0.truncate()
			return id+"\n"	
		else:
			return id+" already loaded\n"

@put('/jobs/new')
def newjob():
	global JOBS
	init_jobs()
	# print request.body.readline()
	DATA = json.loads(request.body.readline())
	ID = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
	JOBS[ID]=DATA
	JOBS[ID]['status']="stopped"
	with open('/app/data/jobs.json', 'r+') as f0:
		f0.seek(0)
		f0.write(json.dumps(JOBS))
		f0.truncate()	
	return ID+"\n"

@get('/jobs/delete/<id>')
def deletejob(id):
	global JOBS
	init_jobs()
	if id not in JOBS:
		return "not found\n"
	if JOBS[id]['status']=="started":
		return "job still running\n"
	del JOBS[id]
	with open('/app/data/jobs.json', 'r+') as f0:
		f0.seek(0)
		f0.write(json.dumps(JOBS))
		f0.truncate()	
	return id+"\n"

@put('/jobs/set/<id>')
def setjob(id):
	global JOBS
	init_jobs()
	if id not in JOBS:
		return "id not found\n"
	# print request.body.readline()
	DATA = json.loads(request.body.readline())
	for K,V in DATA.iteritems():
		if K=="status" or K=="pid":
			continue			
		JOBS[id][K]=V
	with open('/app/data/jobs.json', 'r+') as f0:
		f0.seek(0)
		f0.write(json.dumps(JOBS))
		f0.truncate() 
	return id+"\n"

@get('/tags/get/epc/<id>')
def getepc(id):
	global JOBS
	init_jobs()	
	
	
	
@error(404)  # Not Found
@error(405)  # Method Not Allowed
@error(500)  # Internal server Error
@app_json
def error_response(error):
    return {
        'Error': response.status_code,
        'Text': HTTP_CODES.get(response.status_code, 'Unknown'),
        'Path': request.path,
        'Method': request.method
    }

if __name__ == '__main__':
	os.system("mount -a")
	os.system("mkdir /app/data/running")
	os.system("cp /app/jobs.json /app/data/jobs.json")
	JOBS = {}
	init_jobs() 
	print json.dumps(JOBS)
	for ID,JOB in JOBS.iteritems():
		if JOB['restart'] == "always":
			print "Starting job: "+ID+" "+JOB['name']+"..."
			if check_pid(JOB['pid']):
				kill_job(ID)
			run_job(ID)
			print "OK"
		time.sleep(0.5)
	time.sleep(2)	
	init_jobs()
	# print json.dumps(JOBS)
	thread.start_new_thread(update_jobs,())
	
	run(host='0.0.0.0', port=80)
