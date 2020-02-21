sudo apt-get update
sudo apt-get install -y python3-pandas python3-sklearn swig bison \
libasound2-dev flac nltk python3-pyaudio

sudo pip3 install SpeechRecognition nltk numpy simpleaudio

#install pocketsphinx
#https://howchoo.com/g/ztbhyzfknze/how-to-install-pocketsphinx-on-a-raspberry-pi
wget https://sourceforge.net/projects/cmusphinx/files/sphinxbase/5prealpha/sphinxbase-5prealpha.tar.gz/download -O sphinxbase.tar.gz
wget https://sourceforge.net/projects/cmusphinx/files/pocketsphinx/5prealpha/pocketsphinx-5prealpha.tar.gz/download -O pocketsphinx.tar.gz
tar -xzvf sphinxbase.tar.gz
tar -xzvf pocketsphinx.tar.gz
cd sphinxbase-5prealpha
./configure --enable-fixed
make
sudo make install
cd ../pocketsphinx-5prealpha
./configure
make
sudo make install






