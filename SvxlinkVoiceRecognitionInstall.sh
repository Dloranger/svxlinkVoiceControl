sudo apt-get update
#install the needed support libraries
sudo apt-get install -y python3-pandas python3-sklearn swig bison \
libasound2-dev flac python3-pyaudio
sudo pip3 install SpeechRecognition numpy simpleaudio nltk

#Download the nltk libraries, #this will take a while
mkdir /usr/share/nltk_data
sudo python3 -m nltk.downloader -d /usr/local/share/nltk_data all

mkdir /temp
mkdir /usr/bin/svxlinkVoiceControl
cd /temp
#Pull down the voice control functionality
git clone https://github.com/Dloranger/svxlinkVoiceControl.git


#
# move the various files to their final location, with permissions
#
cd /svxlinkVoiceControl
rm README.MD
chmod +x *.py
mv *.py /usr/bin/svxlinkVoiceControl/*
# eventually OpenRepeater GUI will stomp on this file, but get 
# a starter file in place for non OpenRepeater users
mv ./local/* /usr/share/svxlink/events.d/local/
# starter config file for a pi-repeater-1x, eventually OpenRepeater
# will stomp on this file as well
mv ./svxlink.conf /etc/svxlink/svxlink.conf
mv /sounds/* /usr/share/svxlink/sounds/en_US/svxlinkVoiceControl/*
mv svxlink.service /lib/systemd/system/svxlink.service








