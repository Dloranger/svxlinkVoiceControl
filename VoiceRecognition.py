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
COS_GPIO = "gpio31"
#PathToGpioValue = "/sys/class/gpio/"+COS_GPIO+"/value"
PathToGpioValue = "./tmp.tmp"

# what should the wake-work of the system be? 3-4 syllables, 1 word
    
#WakePhrase = "hey aurora"
#WakePhrase = "hey zulu"
WakePhrase = 'Aragorn'
#what language to use "english"
language = "english"

#How long should be allowed for the command (COS) to come in after the wakeup
TimeOutCounterInitial = 600 # n*0.01 seconds

#load dependencies
import numpy as np
import pandas as pd
import time
import importlib as imp
#holds the misc voice functions used in this script
import VoiceRecognitionFunctions as VRF 
import GeneralFunctions as func # general purpose functions
from sklearn.feature_extraction.text import CountVectorizer # for bag of words

from os import path



# Where does the system store the recorded audio
PathToAudioFile = "Speak.wav"

# set debugging verbose to 0 for quiet logs, set to 1 for traceable outputs
verbose = 1

#code assumes COS is active low logic type
COS = func.UpdateCOSValue (PathToGpioValue) #get initial value
while True : 
	
	func.DebugMessage (verbose,"Waiting for the wakeup command")
	
	#Waiting for the COS to be triggered, aka "idle state", do not use timeout
	func.WaitForCOSToggle("0", -1,PathToGpioValue)
	# Cos is now active
	func.DebugMessage (verbose,"Waiting 5 seconds for the COS to release")
	# if note timing out, then we want to translate
	TranslateDisable = func.WaitForCOSToggle("1", 500,PathToGpioValue)
	func.DebugMessage (verbose,TranslateDisable)
	
	if TranslateDisable:
		func.WaitForCOSToggle("1", -1,PathToGpioValue)
	else:
		func.DebugMessage (verbose,"COS has been released, translating text \n\
	looking for wake word")	
	# Cos is now inactive
	
	##### TODO
	# Replace this conversion with a live audio capture of the first n sec of
	# live audio, this should be UDP streamed from SVXLINK, see the howto linked
	# above for setting the svxlink side up
	if not TranslateDisable:
		Text = VRF.ConvertAudioToText(verbose,
										PathToAudioFile,
										OnlineTranslationAllowed,
										OnlineTranslationService)
										#Tokenize the result
		textList = Text.split()
	else:
		textList = [" "," "]
	
	if WakePhrase == textList[0] or WakePhrase == textList [1]: 
		func.DebugMessage (verbose,"Wakeup word detected")
				 
		#Indicate to the user the system is listening
		#Play some audio file back to the audio output, ENSURE PTT stays active
		#playAudio ("The King is listening")
		func.DebugMessage (verbose,"playing sound \"Repeater is listening\"")
		VRF.PlayWaveAudioSimpleAudio('./Sounds/RepeaterListening.wav')
		
		# assume the cos signal is still idle when we get this far
		func.DebugMessage (verbose,"waiting for command to arrive")
		CommandArrived = func.WaitForCOSToggle("0",500,PathToGpioValue)
		
		# only watch for a while for short time so the system doesn't get out of
		# sync, and commands should not be very long winded.  Check for a 
		# timeout first since its the minimal code, easier than finding it 
		# later buried down in the code. 
		#
		# 10 seconds seems like a fair compromise of ~5 seconds to initiate the
		# sending of the command, and also ending the commands, so we are only 
		# looking for the squelch to close now.
		if (CommandArrived or func.WaitForCOSToggle("1",500,PathToGpioValue)):
			func.DebugMessage (verbose,"Timeout waiting for command to arrive")
		else: 
			#we didn't time out, so we must have gotten some audio to process
			#COS has opened, collect the audio
			### To be implemented
			func.DebugMessage (verbose,"Command has been received")
			
			# prepare to try to figure out what the user is requesting, this is 
			# where some machine learning process comes into play
			cleanText = VRF.CleanText(Text,language)
			
			# Apply the model to predict what user wants based on audio received
			# new commands will need to have the models built with new sample
			# audio files so the model can learn how to handle them
			
			func.DebugMessage (verbose,"doing something with NLP results")
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