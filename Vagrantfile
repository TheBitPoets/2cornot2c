# -*- mode: ruby -*-
# vi: set ft=ruby :

require "rbconfig"

box_file = File.join(__dir__, ".classroom-box")
box_name = ENV["CLASSROOM_BOX_NAME"]
box_name = File.read(box_file, encoding: "UTF-8").strip if box_name.to_s.empty? && File.file?(box_file)
box_name = "bento/ubuntu-24.04" if box_name.to_s.empty?
unless box_name.match?(/\A[A-Za-z0-9._-]+\/[A-Za-z0-9._-]+\z/)
  raise "Nome box non valido in .classroom-box o CLASSROOM_BOX_NAME."
end

memory_mb = Integer(ENV.fetch("CLASSROOM_MEMORY_MB", "2048"), 10)
raise "CLASSROOM_MEMORY_MB deve essere tra 1024 e 8192." unless (1024..8192).cover?(memory_mb)
prebuilt_classroom_box = box_name != "bento/ubuntu-24.04"

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://vagrantcloud.com/search.
  # Bento publishes amd64 and arm64 variants for VirtualBox and VMware, so the
  # same Vagrantfile works on Windows and on Apple Silicon.
  config.vm.box = box_name
  config.vm.hostname = "2cornot2c"
  config.vm.boot_timeout = 900

  # VirtualBox on Apple Silicon can start the ARM framebuffer before it is
  # ready, leaving an otherwise healthy XFCE session black. Restarting only
  # the display manager after Vagrant has completed boot and mounts fixes it
  # without affecting Windows/amd64 guests.
  config.trigger.after :up do |trigger|
    trigger.name = "Recover the graphical session on Apple Silicon"
    trigger.run_remote = {
      inline: "if [ \"$(uname -m)\" = aarch64 ] && command -v VBoxControl >/dev/null; then sudo systemctl restart lightdm; fi"
    }
  end

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # NOTE: This will enable public access to the opened port
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine and only allow access
  # via 127.0.0.1 to disable public access
  # config.vm.network "forwarded_port", guest: 80, host: 8080, host_ip: "127.0.0.1"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
   config.vm.synced_folder "./lab", "/lab"
   config.vm.synced_folder "./lab2", "/lab2"
  # Disable the default share of the current code directory. Doing this
  # provides improved isolation between the vagrant box and your host
  # by making sure your Vagrantfile isn't accessible to the vagrant box.
  # If you use this you may want to enable additional shared subfolders as
  # shown above.
  # config.vm.synced_folder ".", "/vagrant", disabled: true

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
   config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
    vb.gui = true
    vb.customize ["modifyvm", :id, "--clipboard-mode", "bidirectional"]
    vb.customize ["modifyvm", :id, "--drag-and-drop", "bidirectional"]
    if RbConfig::CONFIG["host_cpu"].match?(/arm64|aarch64/)
      # qemuramfb has no reliable dynamic resizing on Apple Silicon. Keep its
      # stable 1280x800 mode and enlarge it in a scaled host window instead.
      vb.customize ["setextradata", :id, "GUI/Scale", "true"]
      vb.customize ["setextradata", :id, "GUI/LastScaleWindowPosition", "80,80,1152,720"]
      vb.customize ["setextradata", :id, "GUI/RestrictedRuntimeViewMenuActions", "GuestAutoresize"]
    end
  #  vb.customize ["storageattach", :id, "--storagectl", "IDE Controller", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", "emptydrive"]
  #
  #   # Customize the amount of memory on the VM:
    vb.memory = memory_mb
    vb.cpus = 2
   end

   config.vm.provider "vmware_desktop" do |vmware|
     vmware.gui = true
     vmware.allowlist_verified = true
     vmware.vmx["memsize"] = memory_mb.to_s
     vmware.vmx["numvcpus"] = "2"
   end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Enable provisioning with a shell script. Additional provisioners such as
  # Ansible, Chef, Docker, Puppet and Salt are also available. Please see the
  # documentation for more information about their specific syntax and use.
   unless prebuilt_classroom_box
     config.vm.provision "shell", inline: <<-SHELL
     export DEBIAN_FRONTEND=noninteractive
     apt-get update
     apt-get install -y gcc gdb vim make build-essential git xfce4 lightdm
     echo "vagrant:vagrant" | chpasswd
     usermod -aG nopasswdlogin vagrant
     install -d -m 0755 /etc/lightdm/lightdm.conf.d
     printf "%s\n" \
       "[Seat:*]" \
       "autologin-user=vagrant" \
       "autologin-user-timeout=0" \
       "user-session=xfce" \
       > /etc/lightdm/lightdm.conf.d/50-vagrant-autologin.conf
     sudo -u vagrant dbus-run-session -- \
       xfconf-query -c xfwm4 -p /general/use_compositing \
       -n -t bool -s false
     sudo -u vagrant dbus-run-session -- \
       xfconf-query -c xsettings -p /Xft/DPI \
       -n -t int -s 120
     sudo -u vagrant dbus-run-session -- \
       xfconf-query -c xsettings -p /Gtk/FontName \
       -n -t string -s "Sans 11"
     if command -v vmtoolsd >/dev/null && [ -f /vagrant/scripts/change-resolution.sh ]; then
       sed 's/\r$//' /vagrant/scripts/change-resolution.sh \
         > /home/vagrant/cambia-risoluzione.sh
       chown vagrant:vagrant /home/vagrant/cambia-risoluzione.sh
       chmod 0755 /home/vagrant/cambia-risoluzione.sh
     fi
     systemctl disable lightdm-arm-recovery.service 2>/dev/null || true
     rm -f /etc/systemd/system/lightdm-arm-recovery.service
     systemctl daemon-reload
     systemctl set-default graphical.target
   SHELL
     config.vm.provision "shell", inline: <<-SHELL
       if [ -f /etc/X11/Xwrapper.config ]; then
         sed -i 's/allowed_users=.*$/allowed_users=anybody/' /etc/X11/Xwrapper.config
       fi
     SHELL
   end
end
