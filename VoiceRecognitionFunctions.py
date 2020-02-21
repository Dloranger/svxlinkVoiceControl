#!/usr/bin/env python3
import GeneralFunctions as func
import re # regular expressions
import speech_recognition as sr

# natural language tool kit
import nltk 
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer #keep only stem words

#For playing wave files
import pyaudio  
import wave
import simpleaudio as sa

def RecordAudioStreamGoogleSTT():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
	try:
		audioText = r.recognize_google(audio)
		DebugMessage(audioText)
	except sr.UnknownValueError:
		pass
				
def PlayWaveAudioSimpleAudio (PathToAudioFile):
	wave_obj = sa.WaveObject.from_wave_file(PathToAudioFile)
	play_obj = wave_obj.play()
	play_obj.wait_done()  # Wait until sound has finished playing

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
				func.DebugMessage(verbose,"Sphinx thinks you said " + Text)
			except sr.UnknownValueError:
				func.DebugMessage (verbose,"Sphinx could not understand audio")
				return -1
			except sr.RequestError as e:
				func.DebugMessage (verbose,"Sphinx error; {0}".format(e))
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
				func.DebugMessage (verbose,"Google thinks you said: " + Text)
			except sr.UnknownValueError:
				func.DebugMessage (verbose,
					"Google Speech Recognition could not understand audio")
				return -1
			except sr.RequestError as e:
				func.DebugMessage (verbose,
					"Could not request results from Google Speech Recognition \
					{0}".format(e))
				return -1
			return Text
    
		elif OnlineTranslationService == 'Google Cloud':
            # recognize speech using Google Cloud Speech
            #GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""INSERT THE 
			#CONTENTS OF THE GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE HERE""""
			try:
				func.DebugMessage (verbose,
					"Google Cloud Speech thinks you said " +
                      r.recognize_google_cloud(audio, \
                      credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS))
			except sr.UnknownValueError:
				func.DebugMessage (verbose,
					"Google Cloud Speech could not understand audio")
			except sr.RequestError as e:
				func.DebugMessage (verbose,"Could not request results from \
				Google Cloud Speech service; {0}".format(e))
			return Text

def CleanText(TextToClean,language):
	
	#remove misc ascii chars
	text = re.sub('[^a-zA-Z]',' ',TextToClean.lower()) 

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
	
	
