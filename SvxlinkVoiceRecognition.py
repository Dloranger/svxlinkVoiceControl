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
	VRF.DebugMessage (1,"SvxlinkVoiceControl Running")
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
		if (CommandArrived or 
			VRF.WaitForGpioToggle("1",100,PathToCOSGpioValue,verbose)):
			VRF.DebugMessage (verbose,"Timeout waiting for command to arrive")
		else: 
			#stop recording if its still going
			try:
				p.terminate()
			except:
				pass
				
			VRF.DebugMessage (verbose,"Command has been received")
			
			# Send the audio file to get converted to text
			Text = VRF.ConvertAudioToText(verbose,
										PathToAudioFile,
										OnlineTranslationAllowed,
										OnlineTranslationService)
			Text = str(Text) + " of of"  
			Text = Text.lower()
			
			VRF.DebugMessage (verbose,"Processing command")
			# Searches are using lower case letters, be sure to match for new
			# search cases.
			
			# already consumed top level key phrases 
				# sub phrases may be reused due to top level filtering but may
				# not match any of these top level key phrases as they will
				# cause the system to react incorrectly.
				#
				# Keep in mind the search will find these phrases if they are
				# part of a bigger word. for example "id" could be found in
				# "idea", "lid", etc, so be conscious of this implication and 
				# use spaces where it makes sense based on the responses you get
				# back from the translation service.
				#
				# Try to allow for reasonable synanyms where it makes sense so
				# the system can be more tolerant of truly natural language.
			
			# Keep alpha sorted based on first non white space character
			
			################## A ##################
			################## B ##################
			################## C ##################
			################## D ##################
			################## E ##################
			# "echolink"
			# "echo link"
			################## F ##################
			################## G ##################
			################## H ##################
			# "help"
			################## I ##################
			# "identifi" - CleanText result
			################## J ##################
			################## K ##################
			################## L ##################
			################## M ##################
			################## N ##################
			################## O ##################
			################## P ##################
			################## Q ##################
			################## R ##################
			################## S ##################
			################## T ##################
			################## U ##################
			################## V ##################
			################## W ##################
			################## X ##################
			################## Y ##################
			################## Z ##################
			

			if (Text.find("echolink") != -1) or (Text.find("echo link") != -1):
				VRF.DebugMessage (verbose,"Using Echolink Module")
				# Something related to echolink has been requested
				if (Text.find("deactivate") != -1) or \ #close connection
						(Text.find(" disconnect") != -1):
						VRF.DebugMessage (verbose,"Try to deactivate echolink")
						try:
							VRF.ExitModules(PathToPTTGpioValue,verbose)
						except:
							print ("failed to enter exitModules()")
				elif (Text.find(" connect ") != -1) or \ #Open connection
						(Text.find("activate ") != -1):
					VRF.DebugMessage (verbose,"Try to activate echolink")
					try:
						VRF.EcholinkConnect(Text, PathToPTTGpioValue, verbose)
					except:
						print ("failed to connect to Echolink node")
				elif (Text.find("list ")!=-1) and \ #list connections
					(Text.find("connected")!=-1): 
					VRF.DebugMessage (verbose,"List connected nodes requested")
					try:
						VRF.EchoListConnected(PathToPTTGpioValue, verbose)
					except:
						print ("failed to trigger EchoListconnect function")
				elif (Text.find("play ")!=-1) and \ #Play local node
					(Text.find("local")!=-1): 
					VRF.DebugMessage (verbose,"play local node requested")
					try:
						VRF.EchoLinkLocal(Text, PathToPTTGpioValue, verbose)
					except:
						print ("failed to trigger EchoListconnect function")
				else:
					print("Unknown Echolink Command")
					time.sleep (2)
			elif (Text.find("relay")!=-1):
				VRF.DebugMessage (verbose,"Relay command not implemented yet")
				Text = VRF.CleanText(Text,language)
				VRF.DebugMessage (verbose,Text)
			elif (Text.find("help")!=-1):
				# this one can be touchy as the responses might get pretty long
				# and also have to keep in mind there is the help for both the 
				# voice system as well as the help built within svxlink directly
				# which will be different content
				VRF.DebugMessage (verbose,"Help command not implemented yet")
			elif (Text.find("identifi")!=-1):
				VRF.DebugMessage (verbose,"Requesting the system to long ID")
				try:
					VRF.SelfIdentify(PathToPTTGpioValue,verbose)
				except:
					VRF.DebugMessage (verbose,"Failed to self ID") 