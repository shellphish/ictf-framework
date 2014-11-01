This script creates the team and organization VMs.

Usage:
  
    create_vm.py <game_hash>

It will retrieve the JSON configuration for `game_hash` and generate the VMs for it.


It needs:

 - the base VMs as setup (base Ubuntu with no resolvconf and preinstalled dependencies)
 - **sudo access** (so it can guestmount and chroot)
 - the services as `/services/name.deb` and `/services/name/info.json` (and their scripts)
 - the organization VM setup scripts as `/org/` (see create\_vms.py)
 - ability to write in `/game/` and `/var/www/bundles`
 - ability to use qemu-kvm
 - libguestfs-tools (run 'update-guestfs-appliance' if necessary)
 - virtualbox (VBoxManage)
