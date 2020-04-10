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
from SvxlinkVoiceRecognitionConf import * #load the config file



#Find the GPIO for the COS
COS_GPIO = VRF.GetRxCosGpio(RxPortName,SvxlinkConfPath)
PathToCOSGpioValue = PathToGpioPrefix+COS_GPIO+PathToGpioSufix
VRF.DebugMessage (verbose,"RxGPIO:"+PathToCOSGpioValue)

#Find the GPIO for the PTT
PTT_GPIO = VRF.GetTxPTTGpio(TxPortName,SvxlinkConfPath)
PathToPTTGpioValue = PathToGpioPrefix+PTT_GPIO+PathToGpioSufix
VRF.DebugMessage (verbose,"TxGPIO:"+PathToPTTGpioValue)

#Find the OPEN_ON_DTMF Prefix in the svxlink.conf file
DTMFprefix = VRF.GetDTMFOpenString(LogicName,SvxlinkConfPath)

#code assumes COS is active low logic type
COS = VRF.ReadGPIOValue (PathToCOSGpioValue) #get initial value
while True :
	VRF.DebugMessage (1,"SvxlinkVoiceControl Running")
	VRF.DebugMessage (verbose,"Waiting for the wakeup command")
	
	#Waiting for the COS to be triggered, aka "idle state", do not use timeout
	VRF.WaitForGpioToggle("0", 600,PathToCOSGpioValue,verbose)
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
		VRF.DebugMessage (verbose,"COS has been released, translating text")
		VRF.DebugMessage (verbose,"looking for wake word")	
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
		VRF.DebugMessage (verbose,"playing sound \"Repeater is listening\"")
		
		#Waiting for the PTT to be Released, aka "Currently Active", no timeout
		VRF.WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		
		# send audio
		VRF.WriteGPIOValue (PathToPTTGpioValue,1)
		VRF.DebugMessage (verbose,"Turning ON PTT")
		time.sleep(0.2)
		VRF.PlayWaveAudioSimpleAudio('RepeaterListening.wav')
		time.sleep(0.1)
		VRF.DebugMessage (verbose,"Turning OFF PTT")
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
			
			# There will be 2 subsections here, ones that need to be processed
			# with exact wording or contains numbers or other keywords that get
			# stripped out by the cleanText() function.  Where possible, this 
			# cleanText() should be used as it will allow for a lot more works
			# to trigger the command as it will remove the tenses (future/past)
			# and drops the words down to their root words.  This is a trick
			# from the machine learning community to help with flexibility and
			# accuracy
			
			# Section 1: Commands that cannot use the CleanText due to having 
			# key elements stripped out
			if (Text.find("echolink") != -1) or (Text.find("echo link") != -1):
				VRF.DebugMessage (verbose,"Using Echolink Module")
				# Something related to echolink has been requested
				if (Text.find("deactivate") != -1) or \
						(Text.find("disconnect") != -1):
						VRF.DebugMessage (verbose,"Try to deactivate echolink")
						try:
							VRF.ExitModules(PathToPTTGpioValue,verbose)
						except:
							print ("failed to enter exitModules()")
				elif (Text.find("connect") != -1) or \
						(Text.find("activate") != -1):
					VRF.DebugMessage (verbose,"Try to activate echolink")
					try:
						VRF.EcholinkConnect(Text,PathToPTTGpioValue,DTMFprefix,verbose)
					except:
						VRF.DebugMessage (verbose,"Echolink failed to connect")
				else:
					print("Unknown Echolink Command")
					time.sleep (2)
			elif (Text.find("relay")!=-1):
				VRF.DebugMessage (verbose,"Relay command not implemented yet")
			
			# Section 2: Commands that can use the CleanText without issues
			# process the command and strip unused words and bring back to the 
			# root words for maximum flexibility
			else:
				Text = VRF.CleanText(Text,language)
				VRF.DebugMessage (verbose,Text)
				if (Text.find("help")!=-1):
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
