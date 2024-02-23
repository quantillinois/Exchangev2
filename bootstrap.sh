sudo apt update && sudo apt upgrade -y
sudo apt-get install openssh-server gcc g++ make gdb wget iperf tcpdump vim git -y
sudo apt-get install python3 python3-pip -y

sudo apt-get install build-essential libc6 libstdc++6 ca-certificates tar -y

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.12

source /vagrant/exchange-venv/bin/activate