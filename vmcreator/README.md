This script creates the team and organization VMs.

Usage:
  
    create_vm.py <game_id> <num_teams> [service1 service2 ...]


It needs:

 - **sudo access** (so it can guestmount and chroot)
 - the services as `/services/name.deb`
 - the organization VM setup scripts as `/org/a_script.sh`, `/org/another_script.sh`, etc. (Note: all files in /org will be copied to /org on the VM)
 - ability to write in `/game/`
 - ability to use qemu-kvm
 - libguestfs-tools (run 'update-guestfs-appliance' if necessary)
 - virtualbox
 - gdebi-core (on the VM)
