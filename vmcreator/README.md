This script creates the team and organization VMs.

Usage:
  
    create_vm.py <game_hash>

It runs on our web site (http://ictf.cs.ucsb.edu/framework/#/framework): it retrieves the JSON configuration for `game_hash` and generates the VMs for it. Once generated, the VMs are independent from our web site.

Besides the JSON configuration, it needs:

 - the base VMs as setup (base Ubuntu with no resolvconf and preinstalled dependencies - you can get ours at http://ictf.cs.ucsb.edu/base-vms/base-vms.tar.gz)
 - **sudo access** (so it can guestmount and chroot)
 - the services as `/services/name.deb` and `/services/name/info.json` (and their scripts)
 - the organization VM setup scripts as `/org/` (see create\_vms.py)
 - ability to write in `/game/` and `/var/www/bundles`
 - ability to use qemu-kvm
 - libguestfs-tools (run 'update-guestfs-appliance' if necessary)
 - virtualbox (VBoxManage)

*Note:* the VMs, as generated, use a single VirtualBox internal network. Test it, then setup a real game network using the documentation in the `router/` directory.
