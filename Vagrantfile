node = [
  { :hostname => 'exchange', :ip => '192.168.56.20', :box => 'relativkreativ/ubuntu-20-minimal'},
]


Vagrant.configure(2) do |config|
  node.each do |node|
    config.vm.define node[:hostname] do |node_config|
      node_config.vm.box = node[:box]
      node_config.vm.network "private_network", ip: node[:ip]
      node_config.vm.hostname = node[:hostname]
    end
  end

  config.vm.provision "shell", path: "bootstrap.sh", privileged: true

  config.vm.synced_folder "./", "/new-exchange", owner: "vagrant",
    group: "vagrant"
end

