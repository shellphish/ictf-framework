# Base Host

This directory contains the files necessary to create the base host used for the infrastructure components, and, possibly, the vulnerable image.

The system uses [Packer](https://www.packer.io/) to generate a series of artifacts, including:
- A [Vagrant](https://www.vagrantup.com/) box
- An OVA image created from the Ubuntu ISO that can be used as a basis to build additional Vagrant boxes, or to create an AMI in AWS (not working at the moment due to kernel incompatibilities)
- An AMI in AWS that can be used as a basis for other AMIs 

Once the base host has been created, all the other hosts should use this host as a basis, and use exclusively [Ansible](https://www.ansible.com/) to customize the installation.

## Environment Variables

In order for the builder to work, the AWS-related environment variables need to be set.
This is easily achieved by setting the correct values in `scripts/aws_env.sh` and then execute:
```
source scripts/aws_env.sh
```

## Scripts Directory

The scripts directory contain scripts to perform basic initialization, install ansible, and perform cleanup.

Note: the update/upgrade command is complicated to bypass a grub problem.

## Ansible Directory

The ansible subdir contains the ansible playbook that configures the base host.

## HTTP Directory

This directory contains the preseed file used to drive the Ubuntu installer.

## AWS vmimport Directory

In order to import an OVA file into AWS so that it becomes an AMI, it is necessary to create the vmimport role.
This is described in the [AWS Documentation](https://docs.aws.amazon.com/vm-import/latest/userguide/vmimport-image-import.html).

The files assume that one has created an S3 bucket called `ictf-framework-data`.

## Commands

To build the various artifacts use:
```
packer build basehost.json
```

If there is a directory named `iso` with the ISO of the server (which must match the SHA256 checksum in the configuration file)

If one wants to build only a specific version (e.g., only the amazon-ebs instance) it is possible to specify the builder:
```
packer build -only=amazon-ebs basehost.json
```

The output artifacts will be created in the directory `builds`.
When running the script again use the `-force` flag to overwrite its contents, or simply rename it or delete it.