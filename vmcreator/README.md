This script creates the team and organization VMs.

Usage:
  
    create_vm.py <game_id> <num_teams> [service1 service2 ...]


It needs:

 - the base VMs as setup (base Ubuntu with no resolvconf and preinstalled dependencies)
 - **sudo access** (so it can guestmount and chroot)
 - the services as `/services/name.deb` and `/services/name/info.json` (and their scripts)
 - the organization VM setup scripts as `/org/` (see create\_vms.py)
 - ability to write in `/game/` and `/var/www/bundles`
 - ability to use qemu-kvm
 - libguestfs-tools (run 'update-guestfs-appliance' if necessary)
 - virtualbox (VBoxManage)
