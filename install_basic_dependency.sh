apt update
apt install git wget unzip gcc make -y
wget https://github.com/wolfcw/libfaketime/archive/refs/tags/v0.9.9.zip
unzip v0.9.9.zip
cd libfaketime-0.9.9/
make install