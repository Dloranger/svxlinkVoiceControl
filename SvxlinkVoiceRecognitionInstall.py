sudo apt-get update
sudo apt-get install -y python3-pandas python3-sklearn swig bison \
libasound2-dev flac python3-pyaudio

sudo pip3 install SpeechRecognition numpy simpleaudio nltk

mkdir /usr/share/nltk_data
#this will take a while
sudo python3 -m nltk.downloader -d /usr/local/share/nltk_data all







