#!/usr/bin/env python3

import re # regular expressions
import speech_recognition as sr
import time
import subprocess

# natural language tool kit
import nltk 
#nltk.path.append('/home/root/nltk_data/')
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer #keep only stem words

#For playing wave files
import pyaudio  
import wave
import simpleaudio as sa
def GetRxCosGpio(RxPortName,SvxlinkConfPath):
	f=open(SvxlinkConfPath, "r")
	if f.mode == 'r':
		configFile =f.read()
		RxStart = configFile.find("["+RxPortName+"]")
		# trim down the file to just what we care about
		try:
			#400 seems like a reasonable limit to the number of characters
			configFile = configFile[RxStart:ReceiverStart+400]
		except:
			# just in case 400 is too many, just take to the end of the file
			configFile = configFile[RxStart:]
		GPIO_SQL_PIN = configFile[configFile.find("GPIO_SQL_PIN=")+13:
								configFile.find("GPIO_SQL_PIN=")+20]
		#trim any whitespace that might have been captured
		GPIO_SQL_PIN = GPIO_SQL_PIN.rstrip()
		return str(GPIO_SQL_PIN)
	else:
		return -1

def GetTxPTTGpio(TxPortName,SvxlinkConfPath):
	f=open(SvxlinkConfPath, "r")
	if f.mode == 'r':
		configFile =f.read()
		TxStart = configFile.find("["+TxPortName+"]")
		# trim down the file to just what we care about
		try:
			#400 seems like a reasonable limit to the number of characters
			configFile = configFile[TxStart:ReceiverStart+400]
		except:
			# just in case 400 is too many, just take to the end of the file
			configFile = configFile[TxStart:]
		PTT_PIN = configFile[configFile.find("PTT_PIN=")+8:
								configFile.find("PTT_PIN=")+15]	
		#trim any whitespace that might have been captured
		PTT_PIN = PTT_PIN.rstrip()
		return str(PTT_PIN)
	else:
		return -1
	
def RecordAudioStreamGoogleSTT():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
	try:
		audioText = r.recognize_google(audio)
		DebugMessage(audioText)
	except sr.UnknownValueError:
		pass
				
def PlayWaveAudioSimpleAudio (AudioFile):
	try:
		wave_obj = sa.WaveObject.from_wave_file("/usr/share/svxlink/sounds/en_US/" \
		+"svxlinkVoiceControl/"+AudioFile)
		play_obj = wave_obj.play()
		play_obj.wait_done()  # Wait until sound has finished playing
	except:
		#Display the warning no matter the setting, this needs to be
		#known to the user
		DebugMessage(1,"SVR **** WARNING **** AudioFile failed to play")
	
def ConvertAudioToText(verbose,
					PathToAudioFile,
					OnlineTranslationAllowed,
					OnlineTranslationService):
	AUDIO_FILE = PathToAudioFile
	r = sr.Recognizer()
	with sr.AudioFile(AUDIO_FILE) as source:
		audio = r.record(source)  # read the entire audio file

	Text = ""    
	if OnlineTranslationAllowed == True:
        # Choose which online voice processor to use, most have some fees 
        # and requires an account with automatic billing.
		if OnlineTranslationService == 'Sphinx':
            ## recognize speech using Sphinx (online version?),
			try:
				Text = r.recognize_sphinx(audio)
				DebugMessage(verbose,"Sphinx thinks you said " + Text)
			except sr.UnknownValueError:
				DebugMessage (verbose,"Sphinx could not understand audio")
				return -1
			except sr.RequestError as e:
				DebugMessage (verbose,"Sphinx error; {0}".format(e))
				return -1
    
		elif OnlineTranslationService == 'Google':
			try:
        # the default api has a meaningful lag, not sure if this will improve
        # with a paid api or not.
        # for testing purposes, we're just using the default API key
        # to use another API key, use 
        # `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
				Text = r.recognize_google(audio)
				DebugMessage (verbose,"Google thinks you said: " + Text)
			except sr.UnknownValueError:
				DebugMessage (verbose,
					"Google Speech Recognition could not understand audio")
				return -1
			except sr.RequestError as e:
				DebugMessage (verbose,
					"Could not request results from Google Speech Recognition \
					{0}".format(e))
				return -1
			return Text
    
		elif OnlineTranslationService == 'Google Cloud':
            # recognize speech using Google Cloud Speech
            #GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""INSERT THE 
			#CONTENTS OF THE GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE HERE""""
			try:
				DebugMessage (verbose,
					"Google Cloud Speech thinks you said " +
                      r.recognize_google_cloud(audio, \
                      credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS))
			except sr.UnknownValueError:
				DebugMessage (verbose,
					"Google Cloud Speech could not understand audio")
			except sr.RequestError as e:
				DebugMessage (verbose,"Could not request results from \
				Google Cloud Speech service; {0}".format(e))
			return Text

def CleanText(TextToClean,language):
	
	#remove misc ascii chars
	text = re.sub('[^a-zA-Z0-9]',' ',TextToClean.lower()) 

    #split the string into list of words
	text = text.split()
    # remove non-significant words ("the" "in" etc, apply stem word 
    # function inline
	ps = PorterStemmer()
	text = [ps.stem(word) for word in text if not word in 
		set(stopwords.words(language))]

    #revert the fixed up list of words back to a string
	text = ' '.join(text)
	return text
		
def DebugMessage (verbose,Message):
	if verbose:
		for i in range (6):
			try:
				f = open("/var/log/svxlink", "a")
				f.write("SVXLINK_VOICE: "+Message+"\n")
				f.close()
				return 0
			except:
				pass
				#likely the file is already open by svxlink
		return -1		
				
			
		
				
def ReadGPIOValue (PathToGpioValue):
	f=open(PathToGpioValue, "r")
	if f.mode == 'r':
		GPIO =f.read()
	return str(GPIO)
	
def WriteGPIOValue (PathToGpioValue,Value):
	f=open(PathToGpioValue, "w")
	if f.mode == 'w':
		f.write(str(Value))
		return 0
	else:
		return -1
		
def WaitForGpioToggle (InitialValue,Timeout,PathToGpioValue,verbose):
	#DebugMessage (verbose,"Entered WaitForGPIOToggle")
	while Timeout != 0:
		# when reading the file we get a line return, need to ignore it
		#DebugMessage (verbose,"Timeout:"+str(Timeout))
		GPIO = ReadGPIOValue(PathToGpioValue).replace('\r\n', '').replace('\n', '')
		#DebugMessage (verbose,"GPIO:"+str(GPIO))
		#DebugMessage (verbose,"INIT:"+InitialValue)
		if GPIO == InitialValue:
			if Timeout != -1:
				Timeout = Timeout-1
				
			if Timeout == 0:
				DebugMessage (verbose,"Timeout occured")
				return -1	
		else:
			if (InitialValue == "0" and GPIO == "1") or \
				(InitialValue == "1" and GPIO == "0"):
				#DebugMessage (verbose,"Confirmed GPIO Toggle")
				return 0
		time.sleep (0.1)
	
############################################################################
############################################################################
#																		   #
#    FUNCTIONS THAT INTERACT WITH THE DTMF SYSTEM WITHIN SVXLINK		   #
#																		   #
############################################################################
############################################################################
	
# basic console syntax to send a message is 
	# echo 212*<code to send># | nc -q 1 127.0.0.1 10000
	# note without the '-q 1' flag, the command will never terminate
	# this flag tells it to quit after 1 second which is plenty fast for
	# what we need to do
			
def EcholinkActivate(verbose);	
		try:
			# activate echolink module
			cmd = 'echo *#2# | nc -q 1 127.0.0.1 10000'
			p = subprocess.Popen(cmd, shell=True)
			#wait for the system to stop talking
			WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
			#just a bit of extra margin
			time.sleep (0.2)
		except:
			DebugMessage (verbose, "failed to activate to EchoLink module")
			
			
def EchoLinkLocal(Text, PathToPTTGpioValue, verbose):
	try:
		# activate echolink module
		EcholinkActivate(verbose)
		#send the play local node command
		cmd = 'echo *2# | nc -q 1 127.0.0.1 10000'
		p = subprocess.Popen(cmd, shell=True)
		#wait for the system to stop talking
		WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		#just a bit of extra margin
		time.sleep (0.2)
	except:
		DebugMessage(verbose,"Failed to send EchoLinkLocal command")	
		
def EchoListConnected(PathToPTTGpioValue, verbose):
	try:
		# activate echolink module
		EcholinkActivate(verbose)
		#send the list active nodes command
		cmd = 'echo *2# | nc -q 1 127.0.0.1 10000'
		p = subprocess.Popen(cmd, shell=True)
		#wait for the system to stop talking
		WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		#just a bit of extra margin
		time.sleep (0.2)
	except:
		DebugMessage(verbose,"Failed to send EchoListConnected command")
	
def EcholinkConnect (Text,PathToPTTGpioValue,verbose):
	Node_ID = re.findall(r"(?:\s*\d){4,6}", Text)
	Node_ID = str(Node_ID[0])
	Node_ID = Node_ID.replace(" ","")
	DebugMessage (verbose, Node_ID)					
	# make sure the length is long enough to have a chance of working
	try:
		# activate echolink module
		cmd = 'echo *2# | nc -q 1 127.0.0.1 10000'
		p = subprocess.Popen(cmd, shell=True)
		#p = subprocess.check_call(cmd, shell=True)
		#DebugMessage (verbose, p)	
		#wait for the system to stop talking
		WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		#just a bit of extra margin
		time.sleep (0.5)
						
		# connect to the target node
		cmd = "echo *"+str(Node_ID)+"# | nc -q 1 127.0.0.1 10000 "
		p = subprocess.Popen(cmd, shell=True)
		# wait for the system to stop talking
		WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
	except:
		DebugMessage (1, "Echolink connection failed")
		ExitModules()
		
def ExitModules(PathToPTTGpioValue,verbose):
		try:
			DebugMessage (verbose, "Entered Exit Modules command")
			#wait for the system to stop talking
			WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
			cmd = "echo *## | nc -q 1 127.0.0.1 10000"
			p = subprocess.Popen(cmd, shell=True)
			#wait for the system to stop talking
			WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		except:
			DebugMessage (1, "Failed to send Exit Modules command")
		
def Relays(PathToPTTGpioValue,verbose):
	### FUNCTION NOT IMPLEMENTED YET
		
	#cmd = "echo *## | nc -q 1 127.0.0.1 10000"
	#p = subprocess.Popen(cmd, shell=True)
	#wait for the system to stop talking
	WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		
def SelfIdentify (PathToPTTGpioValue,verbose):
	try:
		#wait for the system to stop talking
		WaitForGpioToggle("1", -1,PathToPTTGpioValue,verbose)
		# "*" DTMF command forces the system to self ID
		# not sure why this needs to be *#*#, but it works reliably
		# while *#* does not
		cmd = "echo *#*# | nc -q 1 127.0.0.1 10000"
		p = subprocess.Popen(cmd, shell=True)
	except:
		DebugMessage(1, "Failed to Self ID")
		
def CreatePredictionModel (DataSet):
	### some stuff for later when more advanced machine learning can be implemented
# ignore for now

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