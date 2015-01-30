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

Besides the JSON configuration, it needs:

 - the base VMs as setup (base Ubuntu with no resolvconf and preinstalled dependencies - you can get ours at http://ictf.cs.ucsb.edu/base-vms/base-vms.tar.gz)
 - **sudo access** (so it can guestmount and chroot)
 - the services as `/services/name.deb` and `/services/name/info.json` (and their scripts)
 - the organization VM setup scripts as `/org/` (see create\_vms.py)
 - ability to write in `/game/` and `/var/www/bundles`
 - ability to use qemu-kvm
 - libguestfs-tools (run 'update-guestfs-appliance' if necessary)
 - virtualbox (VBoxManage)
 - Don't forget to register your base VMs with virtualbox

*Note:* the VMs, as generated, use a single VirtualBox internal network. Test it, then setup a real game network using the documentation in the `router/` directory.
