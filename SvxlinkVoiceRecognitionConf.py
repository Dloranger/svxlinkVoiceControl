# set debugging verbose to 0 for quiet logs, set to 1 for detailed outputs
verbose = 1

# Port Information, where to read other config stuff from
LogicName = 'ORP_RepeaterLogic_Port1'
RxPortName = 'RX_Port1'
TxPortName = 'TX_Port1'

################## Configure the behavior of the system ########################
# should we allow the use of online services?  The online services when
# available will be far better at converting audio to text, but internet
# may not always be available to all sites, so an offline approach needs
# to be available as well. use "True" or "False"
OnlineTranslationAllowed = True

#How long should be allowed for the command (COS) to come in after the wakeup
TimeOutCounterInitial = 60 # n*0.1 seconds

# Which online translator to use
OnlineTranslationService = 'Google'   #should work for most uses and is free
#OnlineTranslationService = 'DeepVoice' # Not implemented yet
#OnlineTranslationService = 'Sphinx' # Not implemented yet

# what should the wake-work of the system be? 3-4 syllables, 1 word
WakePhrase = 'Aurora'

#what language to use "english"
language = "english"

# Where does the system store the recorded audio (tempfs to record to ramdisk)
PathToAudioFile = '/dev/recordedAudio.wav'

#where to find the GPIO signals in the file system
PathToGpioPrefix = "/sys/class/gpio/"
PathToGpioSufix = "/value"

# Where to find the SVXlink config file
SvxlinkConfPath = '/etc/svxlink/svxlink.conf'