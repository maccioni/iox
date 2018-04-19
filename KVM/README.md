# How to build an CentOS 7 VM for Cisco IOS XE devices

step-by-step instruction tobuild a CentOS 7 VM to be hosted in a
Cisco IOS XE device like a Cisco Catalyt 9000

# Requirements

These are the requirements:
* A CentOS 7 server installed in a virtualization platform like
  Virtual Box
* A Cisco device running IOS Xe 16.8.1 or later
* Docker Community Edition (CE)
* qemu-img converter
* ioxclient to create an IoX package
* A DHCP server or an IP address to make the VM reachable

These are all the steps needed to build the IoX package, load it to the device, activate and start it.

## 1) enable serial port on the CentOS VM

A serial port is need to gain access to the VM from IOS XE.

To enable it on the CentOS VM:
```
systemctl enable serial-getty@ttyS0.service
```
 
To start and test that it works use:
```
systemctl start getty@ttyS0.service
 
systemctl status serial-getty@ttyS0.service
```

## 2) build a qcow2 image

To build an IoX VM based on an existing VM running on a virtualization
platform like Virtual Box you need to convert the VM in a format
supported by KVM like qcow 2 using common tools like qemu-img.

The first step is to extract all the files from the .ova tar file including the .vmdk file (virtual hard disk drives):

```
tar -xvf appliance.ova
qemu-img convert -O qcow2 CentOS7-disk001.vmdk CentOS7-iox.qcow2
```

## 3) create a package descriptor

Create an IoX package descriptor file and name it package.yaml

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
        file: “CentOS7-iox.qcow2"

```

## 4) build the IoX package

To build the IoX package you need to use the ioxclient, release 1.5.1 or
later. You can download it here: [ioxclient](https://developer.cisco.com/docs/iox/#downloads)

```
Mac $ ioxclient package  --name centos7-iox .
```

A file named centos7-iox.tar should be created in the local directory

```
Mac $ ls -l centos7-iox.tar
-rw-r--r--  1 fabrimac  staff  581339648 Apr 17 21:51 centos7-iox.tar
```

## 5) copy the IoX package to the Cisco device

```
Mac $ scp centos7-iox.tar admin@172.26.249.151:
```

## 6) enable IoX on the Cisco IOS XE device

First of all you need to enable iox and wait untill all the services are up

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

## 7) configure the App

You need to configure at least one interface (vnic) per container.
Both management port and up to 4 data ports are supported.
In case of Data ports, you need to configure a VPG (Virtual Port Group)
as well.

Example of configuration with Management port only:
```
app-hosting appid centos7
 vnic management guest-interface 0 gateway 172.26.249.1 name-server 171.70.168.183
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

## 8) Install the App

Now you need to install, activate and start the application.
 
```
Cat9k# app-hosting install appid centos7 package usbflash0:centos7-iox.tar
centos installed successfully
Current state is: DEPLOYED

Cat9k# app-hosting activate appid centos7
centos7 activated successfully
Current state is: ACTIVATED

Cat9k# app-hosting start  appid centos7
centos7 started successfully
Current state is: RUNNING
```

Verify the app status and details

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
   IPv4 address        : 172.26.249.231


Cat9k#
```

## 9) [optional] Connect to the VM and configure Networking

If you have a DHCP server in your network, the VM should automatically
get an IP address as in the example shown above.

If you don't have a DHCP server or if you want to change the IP address,
you can connect to the VM and follow the usual procedure to configure
networking on a Centos 7 server.

To connect to the VM from the IOS XE CLI:

```
Cat9k#app-hosting connect appid centos7 console
Connected to appliance. Exit using ^c^c^c

CentOS Linux 7 (Core)
Kernel 3.10.0-693.el7.x86_64 on an x86_64

localhost login: root
Password:
Last login: Wed Apr 18 12:23:26 from 10.24.80.161
[root@localhost ~]#
```

Verify server ethernet interfaces 

```
[root@localhost ~]# ls /sys/class/net
eth0  lo
```

edit the interface configuration file:

```
[root@localhost ~]# cat /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=none
NAME=eth0
DEVICE=eth0
ONBOOT=yes
DNS1=171.70.168.183
IPADDR=172.26.249.201
PREFIX=24
GATEWAY=172.26.249.1
```

Restart networking
```
[root@localhost ~]# systemctl restart network
```

## 10) Verify VM is reachable from outside the device

Verify from any machine with access to the device

```
Mac:~ $ ping 172.26.249.231
PING 172.26.249.231 (172.26.249.231): 56 data bytes
64 bytes from 172.26.249.231: icmp_seq=0 ttl=59 time=17.640 ms
64 bytes from 172.26.249.231: icmp_seq=1 ttl=59 time=13.931 ms
^C
--- 172.26.249.231 ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 13.931/15.785/17.640/1.855 ms
Mac:~ $
Mac:~ $
Mac:~ $ ssh root@172.26.249.231
root@172.26.249.231's password:
Last login: Wed Apr 18 13:35:17 2018 from 10.24.80.161
[root@localhost ~]#
```

If you are able to connect via SSH, congrats, you have built your own
CentOS 7 VM for Cisco IOS XE devices!!!
