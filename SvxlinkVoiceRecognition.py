#!/usr/bin/env python3
################################################################################
# This script is using a combination of text to speach utilities in
# conjuntion with some machine learning approaches to recognize human
# speech to control the behavior of the system
#
################################################################################

#### Misc notes for later consideration / integrations
#1) https://github.com/sm0svx/svxlink/wiki/RecordAudioFromReceiver - use to 
#   stream the audio into this script for decoding.
#2) a seperate thread should be implemented to record audio to file when the
#	COS is active and terminate it when the COS is inactive.  How to do this??

################## Configure the behavior of the system ########################
# should we allow the use of online services?  The online services when
# available will be far better at converting audio to text, but internet
# may not always be available to all sites, so an offline approach needs
# to be available as well. use "True" or "False"
OnlineTranslationAllowed = True

# Which online translator to use
OnlineTranslationService = 'Google'   #should work for most uses and is free
#OnlineTranslationService = 'DeepVoice' # Not implemented yet
#OnlineTranslationService = 'Sphinx' # Not implemented yet

#PathToCOSGpioValue = "./tmp.tmp"

# what should the wake-work of the system be? 3-4 syllables, 1 word
    
#WakePhrase = "hey aurora"
#WakePhrase = "hey zulu"
WakePhrase = 'Aurora'
#what language to use "english"
language = "english"

#How long should be allowed for the command (COS) to come in after the wakeup
TimeOutCounterInitial = 60 # n*0.1 seconds

#load dependencies
import numpy as np
import pandas as pd
import time
import importlib as imp
import re as re
#holds the misc voice VRFtions used in this script
import SvxlinkVoiceRecognitionFunctions as VRF 
#import GeneralVRFtions as VRF # general purpose VRFtions
from sklearn.feature_extraction.text import CountVectorizer # for bag of words
import subprocess
from os import path

# Where does the system store the recorded audio (tempfs to record to ramdisk)
PathToAudioFile = '/dev/recordedAudio.wav'

# set debugging verbose to 0 for quiet logs, set to 1 for traceable outputs
verbose = 1

##Which Channels use?
RxPortName = "RX_Port1"
COS_GPIO = VRF.GetRxCosGpio(RxPortName,"/etc/svxlink/svxlink.conf")
PathToCOSGpioValue = "/sys/class/gpio/"+COS_GPIO+"/value"
print ("RxGPIO:"+PathToCOSGpioValue)

TxPortName = "TX_Port1"
PTT_GPIO = VRF.GetTxPTTGpio(TxPortName,"/etc/svxlink/svxlink.conf")
PathToPTTGpioValue = "/sys/class/gpio/"+PTT_GPIO+"/value"
print ("TxGPIO:"+PathToPTTGpioValue)

#code assumes COS is active low logic type
COS = VRF.ReadGPIOValue (PathToCOSGpioValue) #get initial value
while True :
	Text = "EchoLink connect 1 2 3 4 5 6"
	
	
	
	
	VRF.DebugMessage (verbose,"Waiting for the wakeup command")
	
	#Waiting for the COS to be triggered, aka "idle state", do not use timeout
	VRF.WaitForGpioToggle("0", -1,PathToCOSGpioValue,verbose)
	# Cos is now active
	VRF.DebugMessage (verbose,"Waiting 5 seconds (max) for the COS to release")
	p = subprocess.Popen(['arecord', '--device=dsnooped','--format','S16_LE', 
	'-d 5','-c 2', '-r 48000',PathToAudioFile],shell=False)

	# if not timing out, then we want to translate
	TranslateDisable = VRF.WaitForGpioToggle("1", 50,PathToCOSGpioValue,verbose)
	#make sure the recording has terminated
	p.terminate()
	time.sleep(0.05)
	
	VRF.DebugMessage (verbose,"TranslateDisable:"+str(TranslateDisable))
	
	if TranslateDisable:
		VRF.WaitForGpioToggle("1", -1,PathToCOSGpioValue,verbose)
	else:
		VRF.DebugMessage (verbose,"COS has been released, translating text \n\
	looking for wake word")	
	# Cos is now inactive
	
	##### TODO
	# Replace this conversion with a live audio capture of the first n sec of
	# live audio, this should be UDP streamed from SVXLINK, see how to linked
	# above for setting the svxlink side up
	if not TranslateDisable:
		# faults will return a -1 so be sure to convert to a string for property
		# operation of the tokenizer
		Text = VRF.ConvertAudioToText(verbose,
										PathToAudioFile,
										OnlineTranslationAllowed,
										OnlineTranslationService)
		#Tokenize the result, make sure at least 2 tokens exist
		Text = str(Text) + " abc def"
		textList = Text.split()
	else:
		textList = [" "," "]
	
	if WakePhrase == textList[0] or WakePhrase == textList [1]: 
		VRF.DebugMessage (verbose,"Wakeup word detected")
				 
		#Indicate to the user the system is listening
		#Play some audio file back to the audio output, ENSURE PTT stays active
		#playAudio ("The King is listening")
		VRF.DebugMessage (verbose,"playing sound \"Repeater is listening\"")
		
		#Waiting for the PTT to be Released, aka "Currently Active", no timeout
		VRF.WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		
		# send audio
		VRF.WriteGPIOValue (PathToPTTGpioValue,1)
		time.sleep(0.2)
		VRF.PlayWaveAudioSimpleAudio('RepeaterListening.wav')
		time.sleep(0.1)
		VRF.WriteGPIOValue (PathToPTTGpioValue,0)
		
		# assume the cos signal is still idle when we get this far
		VRF.DebugMessage (verbose,"waiting for command to arrive")
		CommandArrived = VRF.WaitForGpioToggle("0",100,PathToCOSGpioValue,verbose)
		
		#start recording the command audio (20 sec max)
		p = subprocess.Popen(['arecord', '--device=dsnooped','--format','S16_LE', 
			'-d 20','-c 2', '-r 48000',PathToAudioFile],shell=False)
		
		# looking for the squelch to close now.
		if (CommandArrived or VRF.WaitForGpioToggle("1",100,PathToCOSGpioValue,verbose)):
			VRF.DebugMessage (verbose,"Timeout waiting for command to arrive")
		else: 
			#stop recording if its still going
			try:
				p.terminate()
			except:
				pass
				
			VRF.DebugMessage (verbose,"Command has been received")
			
			# prepare to try to figure out what the user is requesting, this is 
			# where some machine learning process comes into play
			Text = VRF.ConvertAudioToText(verbose,
										PathToAudioFile,
										OnlineTranslationAllowed,
										OnlineTranslationService)
			#Tokenize the result, make sure at least 2 tokens exist, use words
			# that will get stripped away by the CleanText routine
			Text = str(Text) + " of of"  
			Text = Text.lower()
			#textList = Text.split()
			#cleanText = VRF.CleanText(Text,language) # This wipes out numbers
			#VRF.DebugMessage(verbose,"distilled text:" +cleanText)
			
			# Apply the model to predict what user wants based on audio received
			# new commands will need to have the models built with new sample
			# audio files so the model can learn how to handle them
			
			VRF.DebugMessage (verbose,"doing something with NLP results")
			# basic console syntax to send a message is 
			# echo 212*<code to send># | nc -q 1 127.0.0.1 10000
			# note without the '-q 1' flag, the command will never terminate
			# this flag tells it to quit after 1 second which is plenty fast for
			# what we need to do
			if Text.find("echolink") or Text.find("echo link"):
				VRF.DebugMessage (verbose,"doing something with Echolink Module")
				#Something related to echolink has been requested
				# use "disconnect" first before connect as "connect" will be
				# found despite the phrase being "disconnect"
				if Text.find("deactivate") != -1:
					
						VRF.DebugMessage (verbose,"Trying to deactivate")
						VRF.WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
						VRF.ExitModules()						
					
				elif Text.find("connect") != -1:
					try:
						time.sleep (0.1)
						Node_ID = re.findall(r"(?:\s*\d){4,6}", Text)
						Node_ID = str(Node_ID[0])
						Node_ID = Node_ID.replace(" ","")
						print (Node_ID)
						# activate echolink module
						cmd = "echo *2# | nc -q 1 " + \
								"127.0.0.1 10000"
						p = subprocess.Popen(cmd, shell=True)
						
						VRF.WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
						time.sleep (0.5)
						# connect to the target node
						cmd = "echo *"+str(Node_ID)+"# | nc -q 1 " + \
								"127.0.0.1 10000"
						p = subprocess.Popen(cmd, shell=True)
						VRF.WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
					except:
						print ("failed to connect to Echolink node")
				else:
					print("Unknown Echolink Command")
					time.sleep (2)
    
		


#build the prediction model
    
#corpus = []
#for i in range(0,1): #training data size
    #convert the sound clip to raw text
#    TextToReview = VRF.ConvertAudioToText(AudioPaths[i],
#                                         OnlineTranslationAllowed,
#                                         OnlineTranslationService)
    #clean the text and add back to new corpus array
#    corpus.append(VRF.CleanText(TextToReview,language))
        

#Create the "Bag of words model" <aka "tokenizing">
#cv = CountVectorizer()
#X = cv.fit_transform(corpus)