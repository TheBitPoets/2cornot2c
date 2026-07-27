packer {
  required_version = ">= 1.11.0"

  required_plugins {
    vagrant = {
      version = "~> 1.1"
      source  = "github.com/hashicorp/vagrant"
    }
  }
}

variable "source_box" {
  type    = string
  default = "bento/ubuntu-24.04"
}

variable "source_box_version" {
  type    = string
  default = "202510.26.0"
}

variable "output_root" {
  type    = string
  default = "output"
}

source "vagrant" "virtualbox-amd64" {
  communicator = "ssh"
  source_path  = var.source_box
  box_version  = var.source_box_version
  skip_add     = true
  provider     = "virtualbox"
  output_dir   = "${var.output_root}/virtualbox-amd64"
}

source "vagrant" "vmware-arm64" {
  communicator = "ssh"
  source_path  = var.source_box
  box_version  = var.source_box_version
  skip_add     = true
  provider     = "vmware_desktop"
  output_dir   = "${var.output_root}/vmware-arm64"
}

build {
  name = "classroom"
  sources = [
    "source.vagrant.virtualbox-amd64",
    "source.vagrant.vmware-arm64",
  ]

  provisioner "file" {
    source      = "${path.root}/../scripts/change-resolution.sh"
    destination = "/tmp/change-resolution.sh"
  }

  provisioner "shell" {
    scripts = [
      "${path.root}/provision/toolchain.sh",
      "${path.root}/provision/desktop-xfce-minimal.sh",
      "${path.root}/provision/classroom.sh",
      "${path.root}/provision/cleanup.sh",
    ]
    execute_command = "chmod +x '{{ .Path }}'; echo 'vagrant' | sudo -S -E '{{ .Path }}'"
  }
}
