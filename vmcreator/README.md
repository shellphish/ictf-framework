This script creates the team and organization VMs.

    usage: create_vms.py [-h] [--hash GAME_HASH] [--json GAME_JSON]
                         [-o OUTPUT_PATH] [--log LOG_PATH]

    optional arguments:
        -h, --help        show this help message and exit
        --hash GAME_HASH
        --json GAME_JSON
        -o OUTPUT_PATH
        --log LOG_PATH

It can run either on our web site (http://ictf.cs.ucsb.edu/framework/#/framework) or locally.
 * If the option --hash is specified, tt retrieves the JSON configuration for `GAME_HASH` and generates the VMs for it.
 * If the option --json is specified, it reads the file `GAME_JSON` and generates the VMs for it.

If the script runs remotely, the VMs can be downloaded from our website
If the script runs locally, the bundle is created in `OUTPUT_PATH`

Once generated, the VMs are independent from our web site.

# Download and untar the base VMs: base Ubuntu with no resolvconf and preinstalled dependencies
wget http://ictf.cs.ucsb.edu/base-vms/base-vms.tar.gz
tar xzvf base-vms.tar.gz

# Setup the environment to create the VMs (as root)
ln -s /path/to/services /ictf
ln -s /path/to/database /ictf/
ln -s /path/to/dashboard/ /ictf/
ln -s /path/to/scorebot/ /ictf/

# Install required packages (as root)
apt-get install libguestfs-tools virtualbox
update-guestfs-appliance

# Register the base VMs with VirtualBox (as root)
VBoxManage registervm /path/to/base-vms/iCTF-base/iCTF-base.vbox 
VBoxManage registervm /path/to/base-vms/Organization-base/Organization-base.vbox
VBoxManage list vms

# Create VMs described by example\_game.json
sudo python create\_vms.py --json example\_game.json -o /path/to/store/bundle

*Note:* the VMs, as generated, use a single VirtualBox internal network. Test it, then setup a real game network using the documentation in the `router/` directory.
