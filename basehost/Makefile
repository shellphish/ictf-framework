BUILDER := ami
TEMPLATE_DIR := ./build_${AWS_REGION}/composed_templates_$(BUILDER)
#MELT_AMI_NAME := melt_ubuntu_amd64_$(UBUNTU_VERSION)
#HEAT_AMI_NAME := heat_ubuntu_amd64_$(UBUNTU_VERSION)

BUILD_DIR := ./build_${AWS_REGION}
VMS_PRE := $(BUILD_DIR)/vms
VMS_DIR_16.04 := $(VMS_PRE)_16.04
VMS_DIR_18.04 := $(VMS_PRE)_18.04

SECRETS_DIR := ../secrets
OVA_BUILD_DIR := ./build_ova
OVA_VMS_PRE := $(OVA_BUILD_DIR)/vms
OVA_VMS_DIR_18.04 := $(OVA_VMS_PRE)_18.04
OVA_TEMPLATE_DIR := $(OVA_BUILD_DIR)/composed_templates_ova

ALL_VMS_DIRS := $(VMS_DIR_16.04) $(VMS_DIR_18.04)

ALL_MACHINES := $(foreach v, $(shell find ./$(TEMPLATE_DIR)/ -name "$(BUILDER)_cast_*.json"), $(shell basename $(v)))
ALL_MACHINES := $(patsubst $(BUILDER)_cast_%.json, %, $(ALL_MACHINES))
ALL_TARGETS := heat melt teamvm_base teamvm_primed $(ALL_MACHINES:%=cast_%) $(ALL_MACHINES:%=harden_%)
ALL_VMS_ALL_TARGETS := $(ALL_TARGETS:%=$(VMS_DIR_16.04)/%) $(ALL_TARGETS:%=$(VMS_DIR_18.04)/%)
.PHONY: all cast harden init teamvm_ova infra teamvm_ami remote
.PRECIOUS: $(ALL_VMS_ALL_TARGETS)



all: remote teamvm_ova
remote: infra teamvm_ami 
infra: cast harden
teamvm_ami: $(VMS_DIR_18.04)/teamvm_base $(VMS_DIR_18.04)/teamvm_primed
init: $(BUILD_DIR) $(VMS_DIR_16.04) $(VMS_DIR_18.04) $(TEMPLATE_DIR) $(OVA_TEMPLATE_DIR)
cast: $(patsubst %, $(VMS_DIR_16.04)/cast_%, $(ALL_MACHINES))
harden: $(patsubst %, $(VMS_DIR_16.04)/harden_%, $(ALL_MACHINES))

# Below is a little messy, since it doesn't follow the same "heat -> melt -> cast -> harden"
teamvm_ova: $(OVA_VMS_DIR_18.04)/teamvm-primed-ubuntu-18.04.4-server-amd64.ova.gpg

define ansible_role_dependency
    ansible/roles/$(1)/ ansible/roles/$(1)/* ansible/roles/$(1)/*/*
endef

define cast_ansible_role_dependencies
    $(call ansible_role_dependency,$(1)) $(call ansible_role_dependency,register_service_daemon) $(call ansible_role_dependency,common) $(call ansible_role_dependency,common_server)
endef

define vms_dir
    $(strip $(shell basename `dirname $(1)`))
endef

define ubuntu_version
    $(strip $(patsubst vms_%, %, $(call vms_dir, $(1))))
endef


test:
	@echo $(ALL_MACHINES)
	@echo $(ALL_TARGETS)
	@echo $(ALL_VMS_ALL_TARGETS)

$(BUILD_DIR):
	mkdir -p $@

$(VMS_DIR_16.04) $(VMS_DIR_18.04) $(OVA_VMS_DIR_18):
	mkdir -p $@

$(TEMPLATE_DIR): $(wildcard ./packer_composed/*) $(wildcard ./packer_composed/components/*/*)
	rm -f "$(TEMPLATE_DIR)/*"
	mkdir -p "$(TEMPLATE_DIR)"
	./packer_composed/compose_all.sh compose $(TEMPLATE_DIR) ami
	touch $(TEMPLATE_DIR) # the packer_compose updates the contents, not the dir timestamp

$(OVA_TEMPLATE_DIR): $(wildcard ./packer_composed/*) $(wildcard ./packer_composed/components/*/*)
	rm -f "$(OVA_TEMPLATE_DIR)/*"
	mkdir -p "$(OVA_TEMPLATE_DIR)"
	cp ./packer_composed/components/builders/ova_teamvm_base_ubuntu_18.04.json $(OVA_TEMPLATE_DIR)/ova_teamvm_base.json
	cp ./packer_composed/components/builders/ova_teamvm_primed.json $(OVA_TEMPLATE_DIR)/ova_teamvm_primed.json
	touch $@

$(VMS_PRE)_%/heat: $(TEMPLATE_DIR)/$(BUILDER)_heat_%.json $(TEMPLATE_DIR) scripts/live_preconfig_user.sh
	@echo "Building $@"
	$(eval UBUNTU_VERSION=$(call ubuntu_version,$@))
	UBUNTU_VERSION=$(UBUNTU_VERSION) packer build $<
	touch $@

$(VMS_PRE)_%/melt: $(TEMPLATE_DIR)/$(BUILDER)_melt.json $(TEMPLATE_DIR) $(VMS_PRE)_%/heat
	@echo "Building $@"
	$(eval UBUNTU_VERSION=$(call ubuntu_version,$@))
	BASE_IMAGE_NAME=heat_ubuntu_amd64_$(UBUNTU_VERSION) UBUNTU_VERSION=$(UBUNTU_VERSION) packer build $<
	touch $@

$(VMS_DIR_16.04)/cast_%: $(TEMPLATE_DIR)/$(BUILDER)_cast_%.json $(TEMPLATE_DIR) $(VMS_DIR_16.04)/melt $(call cast_ansible_role_dependencies,%) ../%
	@echo "Building $@"
	$(eval UBUNTU_VERSION=$(call ubuntu_version,$@))
	UBUNTU_VERSION=$(UBUNTU_VERSION) BASE_IMAGE_NAME=melt_ubuntu_amd64_$(UBUNTU_VERSION) packer build $<
	touch $@

$(VMS_DIR_16.04)/harden_%: $(TEMPLATE_DIR)/$(BUILDER)_harden.json $(TEMPLATE_DIR) $(VMS_DIR_16.04)/cast_%
	@echo "Building $@"
	$(eval MACHINE=$(strip $(patsubst harden_%, %, $(shell basename $@))))
	$(eval UBUNTU_VERSION=$(call ubuntu_version,$@))
	BASE_IMAGE_NAME=cast_$(MACHINE)_$(UBUNTU_VERSION) IMAGE_NAME="$(MACHINE)" UBUNTU_VERSION=$(UBUNTU_VERSION) packer build $<
	touch $@


$(VMS_DIR_16.04)/teamvm_base $(VMS_DIR_18.04)/teamvm_base: $(TEMPLATE_DIR)/$(BUILDER)_teamvm_base.json $(TEMPLATE_DIR) $(VMS_DIR_16.04)/heat $(VMS_DIR_18.04)/heat scripts/ansible.sh ansible/teamvm_base.yml $(call ansible_role_dependency,teamvm_base) $(call ansible_role_dependency,register_service_daemon)
	@echo "Building $@"
	$(eval UBUNTU_VERSION=$(call ubuntu_version,$@))
	AWS_INSTANCE_TYPE=t2.2xlarge BASE_IMAGE_NAME=heat_ubuntu_amd64_$(UBUNTU_VERSION) UBUNTU_VERSION=$(UBUNTU_VERSION) packer build $<
	touch $@


$(VMS_DIR_16.04)/teamvm_primed $(VMS_DIR_18.04)/teamvm_primed: $(TEMPLATE_DIR)/$(BUILDER)_teamvm_primed.json $(TEMPLATE_DIR) $(VMS_DIR_16.04)/teamvm_base $(VMS_DIR_18.04)/teamvm_base scripts/ansible.sh ansible/teamvm_primed.yml $(call ansible_role_dependency,teamvm_primed) $(call ansible_role_dependency,deploy_ctf_service)
	@echo "Building dockerfiles for $@"
	@echo "Building $@"
	$(eval UBUNTU_VERSION=$(call ubuntu_version,$@))
	AWS_INSTANCE_TYPE=t2.2xlarge BASE_IMAGE_NAME=base_teamvm_$(UBUNTU_VERSION) UBUNTU_VERSION=$(UBUNTU_VERSION) packer build $<
	touch $@


$(OVA_VMS_DIR_18.04)/teamvm-base-ubuntu-18.04.4-server-amd64.ova: $(OVA_TEMPLATE_DIR)/ova_teamvm_base.json
	@echo "Building teamvm base for $@"
	$(eval TMP_DIR=$(shell mktemp -d))
	BUILD_DIR=$(TMP_DIR)/vms packer build $(OVA_TEMPLATE_DIR)/ova_teamvm_base.json
	mkdir -p $(OVA_VMS_DIR_18.04)
	mv $(TMP_DIR)/vms/* $(OVA_VMS_DIR_18.04)/
	rm -rf $(TMP_DIR)


$(OVA_VMS_DIR_18.04)/teamvm-primed-ubuntu-18.04.4-server-amd64.ova: $(OVA_VMS_DIR_18.04)/teamvm-base-ubuntu-18.04.4-server-amd64.ova $(OVA_TEMPLATE_DIR)/ova_teamvm_primed.json
	@echo "Building teamvm primed for $@"
	$(eval TMP_DIR=$(shell mktemp -d))
	BUILD_DIR=$(TMP_DIR)/vms BASE_IMAGE_NAME=$(OVA_VMS_DIR_18.04)/teamvm-base-ubuntu-18.04.4-server-amd64.ova packer build $(OVA_TEMPLATE_DIR)/ova_teamvm_primed.json
	mkdir -p $(OVA_VMS_DIR_18.04)
	mv $(TMP_DIR)/vms/* $(OVA_VMS_DIR_18.04)/
	rm -rf $(TMP_DIR)

$(OVA_VMS_DIR_18.04)/teamvm-primed-ubuntu-18.04.4-server-amd64.ova.gpg: $(OVA_VMS_DIR_18.04)/teamvm-primed-ubuntu-18.04.4-server-amd64.ova $(SECRETS_DIR)/teamvm_ova_key
	@echo "Encrypting teamvm primed"
	rm -rf "$@"
	gpg --batch --passphrase-file $(SECRETS_DIR)/teamvm_ova_key --output "$@" --symmetric "$<"
