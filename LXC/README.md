# How to build a LXC container using Docker tools

step-by-step instruction to build a LXC container to be hosted in a
Cisco IOS XE device like a Cisco Catalyt 9000

# Requirements

These are the requirements:
* A Cisco device running IOS XE 16.8.1 or later
* Docker Community Edition (CE)
* ioxclient to create an IoX package
* A DHCP server or an IP address to make the VM reachable

These are all the steps needed to build the IoX package, load it to the
device, activate and start it. Steps tested on a Linux 16.04.4 LTS server.

# Create a Dockerfile

```
FROM alpine:3.5

RUN apk add --update \
    python3

RUN pip3 install bottle

EXPOSE 8000

COPY main.py /main.py

CMD python3 /main.py
```

# Build the Docker image

```
$ sudo docker build -t iox-cat9k-test .
Sending build context to Docker daemon  14.71MB
Step 1/6 : FROM alpine:3.5
 ---> 6c6084ed97e5
Step 2/6 : RUN apk add --update     python3
 ---> Running in bbf4a5eb4665
fetch http://dl-cdn.alpinelinux.org/alpine/v3.5/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.5/community/x86_64/APKINDEX.tar.gz
(1/11) Installing libbz2 (1.0.6-r5)
(2/11) Installing expat (2.2.0-r1)
(3/11) Installing libffi (3.2.1-r2)
(4/11) Installing gdbm (1.12-r0)
(5/11) Installing xz-libs (5.2.2-r1)
(6/11) Installing ncurses-terminfo-base (6.0_p20171125-r0)
(7/11) Installing ncurses-terminfo (6.0_p20171125-r0)
(8/11) Installing ncurses-libs (6.0_p20171125-r0)
(9/11) Installing readline (6.3.008-r4)
(10/11) Installing sqlite-libs (3.15.2-r1)
(11/11) Installing python3 (3.5.2-r10)
Executing busybox-1.25.1-r1.trigger
OK: 69 MiB in 22 packages
Removing intermediate container bbf4a5eb4665
 ---> 4055557778d1
Step 3/6 : RUN pip3 install bottle
 ---> Running in f7feade2a79a
Collecting bottle
  Downloading https://files.pythonhosted.org/packages/bd/99/04dc59ced52a8261ee0f965a8968717a255ea84a36013e527944dbf3468c/bottle-0.12.13.tar.gz (70kB)
Installing collected packages: bottle
  Running setup.py install for bottle: started
    Running setup.py install for bottle: finished with status 'done'
Successfully installed bottle-0.12.13
You are using pip version 8.1.1, however version 10.0.0 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
Removing intermediate container f7feade2a79a
 ---> 73e27e19ed06
Step 4/6 : EXPOSE 8000
 ---> Running in cf96b4d90bd6
Removing intermediate container cf96b4d90bd6
 ---> 6575aa69d82b
Step 5/6 : COPY main.py /main.py
 ---> d26cfa9719f4
Step 6/6 : CMD python3 /main.py
 ---> Running in ae2fcf22f315
Removing intermediate container ae2fcf22f315
 ---> 42eba0c72563
Successfully built 42eba0c72563
Successfully tagged iox-cat9k-test:latest
```

# Verify Docker image and size

```
$  sudo docker images
REPOSITORY                     TAG                 IMAGE ID            CREATED             SIZE
iox-cat9k-test                 latest              42eba0c72563        10 seconds ago      60.2MB
perfsonar-testpoint.v4.0.iox   latest              289d60bede09        3 weeks ago         959MB
alpine                         3.5                 6c6084ed97e5        3 months ago        3.99MB
hello-world                    latest              f2a91732366c        4 months ago        1.85kB
perfsonar/testpoint            latest              6b69953878b7        5 months ago        959MB

```

# build the IoX package

```
$ sudo ./ioxclient docker package -p ext2 -headroom 200 iox-cat9k-test .
Currently active profile :  default
Command Name:  docker-package
Using the package descriptor file in the project dir
Validating descriptor file package.yaml with package schema definitions
Parsing descriptor file..
Found schema version  2.2
Loading schema file for version  2.2
Validating package descriptor file..
File package.yaml is valid under schema version 2.2
Generating IOx LXC package, type =  lxc
Docker image rootfs size in 1M blocks:  71
Creating iox package with rootfs size in 1M blocks:  271
Parsing Package Metadata file :  /home/user//.package.metadata
Updated package metadata file :  /home/user//.package.metadata
No rsa key and/or certificate files provided to sign the package
Checking if package descriptor file is present..
Skipping descriptor schema validation..
Created Staging directory at :  /tmp/440058382
Copying contents to staging directory
Creating an inner envelope for application artifacts
Generated  /tmp/440058382/artifacts.tar.gz
Calculating SHA1 checksum for package contents..
Parsing Package Metadata file :  /tmp/440058382/.package.metadata
Updated package metadata file :  /tmp/440058382/.package.metadata
Root Directory :  /tmp/440058382
Output file:  /tmp/368740373
Path:  .package.metadata
SHA1 : 0080bca7c1ab53f7479fe053f49c9391afccac53
Path:  artifacts.tar.gz
SHA1 : fa7a0347e046eab3dd768998fc9252b2c0dd5aef
Path:  package.yaml
SHA1 : c8c57090526747f779b46beb78d457b8f6fbf3f5
Generated package manifest at  package.mf
Generating IOx Package..
Package docker image iox-cat9k-test at /home/user//package.tar
```

# Verify package created

```
$ ls -l package.tar 
-rw-r--r-- 1 root root 5632 Apr 17 20:46 package.tar
```
# Configure app

```
Cat9k#conf
Configuring from terminal, memory, or network [terminal]?
Enter configuration commands, one per line.  End with CNTL/Z.
Cat9k(config)#app-hosting appid bottle
Cat9k(config-app-hosting)# vnic management guest-interface 0
Cat9k(config-app-hosting)#end
```

# install, activate and start application

```
Cat9k#app-hosting install appid bottle package usbflash0:lxc-bottle.tar
bottle installed successfully
Current state is: DEPLOYED

Cat9k#app-hosting activate appid bottle
bottle activated successfully
Current state is: ACTIVATED

Cat9k#app-hosting start appid bottle
% Error: Failed
```
