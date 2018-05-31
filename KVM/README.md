# How to build an CentOS 7 VM for Cisco IOS XE devices

In this lab you will learn how to build a CentOS 7 Virtual Machine (VM),
package it in the Cisco Application Framework format, known as IOx (IOS + LinuX)
and host it on a Catalyst 9000 device.

# Requirements

These are the Lab requirements:
* A build server with a virtualization environment like Virtual Box or VMWare
  (ESXi or Fusion). Any Linux server or a Mac would be fine.
  The build server used as a reference is an Ubuntu 16.04.4 LTS server
* A Cisco Catalyst 9000 device running IOS XE 16.8.1 with a front panel USB
  stick of 16GB or bigger. If you don't have a Catalyst 9000 device, you can
  leverage the DevNet Catalyst 9000 Sandbox.
* A DHCP server or a static IP address for the VM

## Step 1: Build the CentOS7 VM

First of all you need to build the base CentOS 7 VM:
* Download CentOS 7 Minimal ISO installer from https://www.centos.org/download/
* Perform default installation making sure the networking is enabled
* Update all the packages using the yum update command:
```
yum -y update
```

## Step 2) enable serial service on the CentOS 7 VM

The Cisco Application Framework provides the option to connect to the VM console
from the IOS XE command line. To make this work, the serial service needs to be
enabled on the VM.

Enable the serial service on the CentOS 7 VM:
```
systemctl enable serial-getty@ttyS0.service
```

Start and verify the service is active:
```
systemctl start getty@ttyS0.service
systemctl status getty@ttyS0.service
```

## Step 3) configure CentOS 7 VM firewall

The firewall service is enabled by default on CentOS.
Firewall rules need to be properly configured depending on the applications you
plan to install on the VM.
For this lab we are going to disable the firewall service:

```
systemctl disable firewalld
systemctl stop firewalld
```

Verify the service is not running anymore:
```
systemctl is-enabled firewalld
systemctl is-active firewalld
```
## Step 4) (optional) configure proxy setting

If the Catalyst 9000 device does not have clear internet access and needs to go
through a proxy server, proxy server settings can be configured in the
~/.bash_profile like in the example below

```
export http_proxy="http://proxy.esl.cisco.com:80"
export https_proxy="https://proxy.esl.cisco.com:80"
```
## Step 5) (optional) install any other application

You can now pre-install any application to the VM so that it will be available
in the Catalyst 9000 device. For instance you can install pip, the Python
packages manager:
```
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y install python-pip
```

To test pip, install any python library like ncclient, a popular python for
NETCONF clients:
```
pip install ncclient
Collecting ncclient
  Downloading https://files.pythonhosted.org/packages/e9/cf/cb131bcaf9b31f8d9d1b9ec3aa9a861dd72a7269a9ff07217b60157fa526/ncclient-0.5.3.tar.gz (63kB)
    100% |████████████████████████████████| 71kB 5.7MB/s
<snip>
  Successfully installed asn1crypto-0.24.0 bcrypt-3.1.4 cffi-1.11.5 cryptography-2.2.2 enum34-1.1.6 idna-2.6 lxml-4.2.1 ncclient-0.5.3 paramiko-2.4.1 pyasn1-0.4.3 pycparser-2.18 pynacl-1.2.1 six-1.11.0  
```

## Step 6) Learn the characteristics of an IOx VM

At this point the VM is ready to be packaged!!

In order to be hosted on a Catalyst 9000 device the VM needs to be pre-packaged
in the IOx format.
An IOx package is a standard tar archive file that contains several files as
shown in the picture below:
![iox characteristics](../iox-package.png?raw=true "IOX characteristics")

* Storage: the VM (or LXC) File System
* Network: the VM virtual interfaces list
* HW Resources Descriptor: a text file with all the HW resources needed to run
  the VM on the Catalyst 9000
* Optional security certificates  

## Step 7) Prepare VM File System Storage

The File System Storage described in the previous step needs to be in the
standard KVM qcow2 format while most of the virtualization platforms create
VM file systems storage in the vmdk (virtual hard disk drives) format instead.

To convert from vmdk to qcow2 format, we are going to use the qemu-img tool in
the Ubuntu build server.

To install the qemu-img tool:

```
apt-get install qemu-guest-agent
apt-get install qemu-utils
```

The next step is to identify the vmdk file in the build server.
It is usually stored in a directory name after the VM in the virtualization
environment main directory, like in the example below:
```
/home/fabrimac/VirtualBox VMs/centos7/centos7.vmdk
```

Note: the vmdk file might have a different file name like centos7-flat.vmdk
      Check the file size and verify which one has the file size of the
      previously create VM.

In case the VM is created in the .ova tar format instead, the vmdk file needs
to be extracted from the ova archive like in the example below:

```
tar -xvf centos7.ova
```

Now using the qemu-img utiliy we can convert the vmdk file to qcow2 format using
the syntax below:
```
qemu-img convert -O qcow2 centos7.vmdk centos7.qcow2
```

Verify the centos7.qcow2 image is present in the local directory.

## Step 8) create the IOx package descriptor

As briefly described before, the HW Resources Descriptor is a text file with
all the HW resources needed to run the VM on the Catalyst 9000.

Create a file in the same directory as the qcow2 image, add the content below
and name it package.yaml

```
descriptor-schema-version: "2.3"

info:
  name: "Cisco IOx KVM Application based on CentOS 7 VM"
  description: "KVM  Application"
  version: "1.0"
  author-link: "http://www.cisco.com"
  author-name: "Cisco Systems"

app:
  # Indicate app type (vm, paas, lxc etc.,)
  type: vm
  cpuarch: "x86_64"
  resources:
    profile: custom
    cpu: 5000
    memory: 1024
    disk: 5
    vcpu: 2

    network:
      -
        interface-name: eth0

  # Specify runtime and startup
  startup:
    disks:
       -
        target-dev: "hdc"
        file: “centos7.qcow2"

```
As you can see, it includes VM info (i.e. name, description, author),
Application type (VM), HW resource (cpu, memory, disk), VM virtual network
interfaces and the VM file system (qcow2 image)

## Step 9) build the IOx package

To build the IOx package you need to use the ioxclient tool (release 1.5.1 or
later) on the build server.
You can download it here: [ioxclient](https://developer.cisco.com/docs/iox/#downloads)

(optional) copy ioxclient to system path (ex. /usr/local/bin) for easier usage.

Verify the qcow2 file name in the package.yaml file matches the actual file name.
Create the IOx package using the syntax below:
```
ioxclient package --name centos7 .
```

A file named centos7.tar should be created in the local directory.
```
ls -l centos7.tar
-rw-r--r-- 1 root root 633184256 May 30 09:53 centos7.tar
```

## Step 10) copy the IOx package to the Cisco device

The CAF/IOx framework on IOS XE will provide several interfaces to manage
the VM as described in the picture below:
![iox management](../iox-management.png?raw=true "IOX Mgmt")

In 16.8.1 only the CLI interface is available and that is what we are going to
use in this lab.

First of all you need to copy the IOx package (the tar file) to the device USB
device:

```
Cat9K# copy scp://fabri@10.10.249.121/centos.tar usbflash0: vrf Mgmt-vrf
```

NOTE: the package cannot be stored in the internal flash for security and
device integrity reasons. The front panel USB 2.0 can be used for testing and
prototyping while for production environments is recommended to use any SSD
storage option available in the given Catalyst 9000 platform (back panel USB 3.0
or M2 SATA).  

## Step 11) enable IOX on the Cisco IOS XE device

Before configuring an VM you need to enable the IOx framework on the device and
wait until all the services are up:
```
Cat9k#conf t
Enter configuration commands, one per line.  End with CNTL/Z.
Cat9k(config)#iox
Cat9k(config)#end
Cat9k#show iox-service

IOx Infrastructure Summary:
---------------------------
IOx service (CAF)    : Running
IOx service (HA)     : Running
IOx service (IOxman) : Running
Libvirtd             : Running
```

## Step 12) configure the App

You need to configure at least one interface (vnic) per VM.
Both management port and up to 4 front panel data ports are supported.
In case of data ports, you need to configure a VPG (Virtual Port Group) as well.
The VPG will serve as default gateway for the container.

Example of configuration with Management port only:
```
app-hosting appid centos7
 vnic management guest-interface 0
```

Example with a data port:
```
Cat9k#conf t
Enter configuration commands, one per line.  End with CNTL/Z.
Cat9k(config)# interface VirtualPortGroup1
Cat9k(config-if)# ip address 10.151.1.1 255.255.255.0
Cat9k(config-if)# app-hosting appid centos7
Cat9k(config-app-hosting)# vnic gateway1 virtualportgroup 1 guest-interface 1
Cat9k(config-app-hosting)#end
```

For this lab let's keep it simple and use the management port only.

If a DHCP server is present in the same network, the VM will get automatically
an IP address.

Following is a simple configuration to enable a DHCP server on a device running
IOS:
```
ip dhcp excluded-address 10.10.249.1 10.10.249.229
ip dhcp pool lab
   network 10.10.249.0 255.255.255.0
   default-router 10.10.249.1
   dns-server 171.70.168.183
   domain-name cisco.com
```

The DHCP server will assign addresses to DHCP clients starting with the IP
address 10.10.249.230

## Step 13) Install the IOx package

Now you need to install, activate and start the IOx package containing the
CentOS 7 VM.

```
Cat9k# app-hosting install appid centos7 package usbflash0:centos7.tar
centos installed successfully
Current state is: DEPLOYED

Cat9k# app-hosting activate appid centos7
centos7 activated successfully
Current state is: ACTIVATED

Cat9k# app-hosting start  appid centos7
centos7 started successfully
Current state is: RUNNING
```

## Step 14) Verify the VM status and details

Use the "sh app-hosting list" CLI to verify the VM has been installed and it is
in running state:
```
cat9k#sh app-hosting list
App id                           State
------------------------------------------------------
centos7                          RUNNING
```

Verify the VM details:
```
Cat9k#show app-hosting detail appid centos7
State                  : RUNNING
Author                 : Cisco Systems
Application
  Type                 : vm
  App id               : centos7
  Name                 : Cisco IOx KVM Application based on CentOS 7 VM
  Version              : 1.0
Activated profile name : custom
  Description          : KVM  Application
Resource reservation
  Memory               : 1024 MB
  Disk                 : 5 MB
  CPU                  : 5000 units
  VCPU                 : 2
Attached devices
  Type              Name        Alias
  ---------------------------------------------
  Serial/shell
  Serial/aux
  Serial/Syslog                 serial2
  Serial/Trace                  serial3

Network interfaces
   ---------------------------------------
eth0:
   MAC address         : 52:54:dd:9c:b3:05
   IPv4 address        : 10.10.249.231
Cat9k#
```

As you can see in the example above the info provided are the same as in the
package.yaml file descriptor plus some state info like the MAC address and the
IP address automatically assigned by the DHCP server.

## Step 15) [optional] Connect to the VM console and configure Networking

If you don't have a DHCP server or if you want to change the IP address, you can
connect to the VM from the IOS XE CLI using the serial service configured at the
very beginning of this lab, and follow the usual procedure to configure
networking on a CentOS 7 server.

To connect to the VM from the IOS XE CLI, use the CLI syntax below and provide
the VM username and password:
```
Cat9k#app-hosting connect appid centos7 console
Connected to appliance. Exit using ^c^c^c

CentOS Linux 7 (Core)
Kernel 3.10.0-693.el7.x86_64 on an x86_64

localhost login: root
Password:
Last login: Wed May 30 09:51:50 from 10.154.133.12
[root@localhost ~]#
```

Verify server ethernet interfaces.
If you recall from previous steps, we configured one VM virtual interface
using the command
```
vnic management guest-interface 0
```

The ending 0 is the interface number, so the VM should have an eth0 interface
only:
```
[root@localhost ~]# ls /sys/class/net
eth0  lo
```

Edit (or create) the eth0 interface configuration script file.
It should look like something like this:
```
[root@localhost ~]# cat /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=none
NAME=eth0
DEVICE=eth0
ONBOOT=yes
DNS1=171.70.168.183
IPADDR=10.10.249.231
PREFIX=24
GATEWAY=10.10.249.1
```

Restart networking
```
[root@localhost ~]# systemctl restart network
```

Verify the eth0 interface is up and has the right IP and gateway configured:
```
[root@localhost ~]# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
<snip>

2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 52:54:dd:bc:76:0c brd ff:ff:ff:ff:ff:ff
    inet 10.10.249.231/24 brd 10.10.249.255 scope global noprefixroute dynamic eth0
```

NOTE: ifconfig is not installed by default on CetntOS 7 minimal.
You can add it if needed:
```
yum install net-tools
```

## Step 16) Verify VM is reachable from outside the device

Verify the VM is reachable from the Ubuntu build server:

```
ping 10.10.249.231
PING 10.10.249.231 (10.10.249.231): 56 data bytes
64 bytes from 10.10.249.231: icmp_seq=0 ttl=59 time=17.640 ms
64 bytes from 10.10.249.231: icmp_seq=1 ttl=59 time=13.931 ms
^C
--- 10.10.249.231 ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 13.931/15.785/17.640/1.855 ms
```

SSH to the VM from the build server:
```
ssh root@10.10.249.231
root@10.10.249.231's password:
Last login: Wed May 30 21:33:18 2018
[root@localhost ~]#
```

If you are able to connect via SSH, congrats, you have successfully built,
configured and loaded your own CentOS 7 VM on a Catalyst 9000 device!!!
