##########################################################################################
##########################################################################################
##### THIS IS STILL AN EARLY DEVELOPMENT PROJECT, MANY FEATURES ARE NOT YET IMPLEMENTED 
##########################################################################################
##########################################################################################
# svxlinkVoiceControl

This project is a python3 application that runs in parallel to SVXlink repeater controller application on a raspberry Pi hardware platform.

To install the project, 

1) first start with an OpenRepeater image (OpenRepeater.com)

####IMPORTANT DO NOT RUN ANY UPDATES ###

2) copy all python files to /usr/bin/svxlinkVoiceControl (new folder you will need to create)
3) copy all sound files (including the folder) to /usr/share/svxlink/sounds/en-us/svxlinkVoiceControl

4) Modify the /local/logics.tcl per https://sourceforge.net/p/svxlink/mailman/message/34798264/

4a)...

4b)...

5) Modify the way svxlink is launched at run time

5a)...

5b)...

6) Configure svxlink/system to provide an audio stream to the python3 script

6a) Configure Rx audio stream

6a1)...

6b) Configure Tx audio stream

6b1)...


7) Make sure the scripts are executable

7a) chmod +x /usr/bin/svxlinkVoiceControl/SvxlinkVoiceRecognition.py

7b) chmod +x /usr/bin/svxlinkVoiceControl/SvxlinkVoiceRecognitionInstall.py

8) ensure all the dependency packages are installed

8a) python3 /usr/bin/svxlinkVoiceControl/SvxlinkVoiceRecognitionInstall.py
