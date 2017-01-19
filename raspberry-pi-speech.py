# coding: utf8

import RPi.GPIO as GPIO
import time
import subprocess, os
import signal
import StringIO
import os.path
import pycurl

from apikeys import GOOGLE_SPEECH_API_KEY

#GPIO overall setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#GPIO input setup
#GPIO 23: Trigger
GPIO_switch = 23
GPIO.setup(GPIO_switch,GPIO.IN, pull_up_down=GPIO.PUD_UP)

#GPIO output setup
#GPIO 18: LED 1
#GPIO 24: LED 2
#GPIO 25: LED 3
#GPIO 17: Error LED
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, 0)
GPIO.setup(24, GPIO.OUT)
GPIO.output(24, 0)
GPIO.setup(25, GPIO.OUT)
GPIO.output(25, 0)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, 0)

#Recording loop variables
recording = 0
command = "arecord -D plughw:1,0 -f cd -t wav -d 0 -q -r 16000 | flac - -s -f --best --sample-rate 16000 -o recording.flac"

def apiRequest():
 #API request variables
 filename = 'recording.flac'

 # API Key can be generated/found here: https://console.cloud.google.com/
 url = 'https://www.google.com/speech-api/v2/recognize?output=json&lang=de-de&key=' + GOOGLE_SPEECH_API_KEY

 #Send 'recording.flac' to Google Speech API v2
 c = pycurl.Curl()
 c.setopt(pycurl.VERBOSE, 0)
 c.setopt(pycurl.URL, url)
 fout = StringIO.StringIO()
 c.setopt(pycurl.WRITEFUNCTION, fout.write)

 c.setopt(pycurl.POST, 1)
 c.setopt(pycurl.HTTPHEADER, [
                'Content-Type: audio/x-flac; rate=16000'])

 filesize = os.path.getsize(filename)
 c.setopt(pycurl.POSTFIELDSIZE, filesize)
 fin = open(filename, 'rb')
 c.setopt(pycurl.READFUNCTION, fin.read)
 c.perform()

 response_code = c.getinfo(pycurl.RESPONSE_CODE)
 response_data = fout.getvalue()

 c.close()
 os.remove("recording.flac")

 #Parse the JSON result string
 start_loc = response_data.find("transcript")
 tempstr = response_data[start_loc+13:]
 end_loc = tempstr.find("\"")
 final_result = tempstr[:end_loc]

 start_loc = response_data.find("transcript")
 tempstr = response_data[start_loc+13:]
 end_loc = tempstr.find("\"")
 responseText = tempstr[:end_loc]

 start_loc = response_data.find("confidence")
 tempstr = response_data[start_loc+12:]
 end_loc = tempstr.find("}")
 confidence = tempstr[:end_loc]

 #Print the result
 print "RAW JSON: " + response_data
 print "You said: " + responseText
 print "Confidence: " + confidence

 #Set GPIO outputs in dependence of the result
 processResult(responseText)

def processResult(resultString):
 resultSplitted = resultString.split(" ")
 for result in resultSplitted:
  print "1"
  if result == "blau":
   GPIO.output(18, 1)
  elif result == "gelb":
   GPIO.output(24, 1)
  elif result == "grün":
   GPIO.output(25, 1)
  else:
   print "else"
   GPIO.output(17, 1)

def resetGPIOs():
 GPIO.output(18, 0)
 GPIO.output(24, 0)
 GPIO.output(25, 0)
 GPIO.output(17, 0)

while True :
 if GPIO.input(GPIO_switch) == 0 and recording == 0:
  resetGPIOs()
  print "Recording..."
  p = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
  recording = 1
  while GPIO.input(GPIO_switch) == 0:
   time.sleep(0.1)
 if GPIO.input(GPIO_switch) == 1 and recording == 1:
  print "Processing..."
  os.killpg(p.pid, signal.SIGTERM)
  apiRequest()
  recording = 0
