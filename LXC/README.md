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
fabri@ubuntu-148# sudo docker build -t iox-bottle .
Sending build context to Docker daemon  12.29kB
Step 1/6 : FROM alpine:3.5
3.5: Pulling from library/alpine
550fe1bea624: Pull complete
Digest: sha256:9148d069e50eee519ec45e5683e56a1c217b61a52ed90eb77bdce674cc212f1e
Status: Downloaded newer image for alpine:3.5
 ---> 6c6084ed97e5
Step 2/6 : RUN apk add --update     python3
 ---> Running in 06f31d654539
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
Removing intermediate container 06f31d654539
 ---> 7ac05c474d1e
Step 3/6 : RUN pip3 install bottle
 ---> Running in feae9410288c
Collecting bottle
  Downloading https://files.pythonhosted.org/packages/bd/99/04dc59ced52a8261ee0f965a8968717a255ea84a36013e527944dbf3468c/bottle-0.12.13.tar.gz (70kB)
Installing collected packages: bottle
  Running setup.py install for bottle: started
    Running setup.py install for bottle: finished with status 'done'
Successfully installed bottle-0.12.13
You are using pip version 8.1.1, however version 10.0.0 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
Removing intermediate container feae9410288c
 ---> dfb99dd55aa5
Step 4/6 : EXPOSE 8000
 ---> Running in 7efa29b99d37
Removing intermediate container 7efa29b99d37
 ---> afecccf80610
Step 5/6 : COPY main.py /main.py
 ---> 8e77957caa6f
Step 6/6 : CMD python3 /main.py
 ---> Running in f26894a22cbe
Removing intermediate container f26894a22cbe
 ---> 2c1f34feddf6
Successfully built 2c1f34feddf6
Successfully tagged iox-bottle:latest
```

# Verify Docker image and size

```
fabri@ubuntu-148# sudo docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
iox-bottle          latest              2c1f34feddf6        3 minutes ago       60.2MB
```

# build the IoX package

```
fabri@ubuntu-148# sudo ioxclient docker package --name iox-bottle.tar iox-bottle .
Saving current configuration
Currently active profile :  default
Command Name:  docker-package
Using the package descriptor file in the project dir
Validating descriptor file package.yaml with package schema definitions
Parsing descriptor file..
Found schema version  2.6
Loading schema file for version  2.6
Validating package descriptor file..
File package.yaml is valid under schema version 2.6
Generating IOx LXC package
Docker image rootfs size in 1M blocks:  71
Creating iox package with rootfs size in 1M blocks:  85
Updated package metadata file :  /root/iox/LXC/.package.metadata
No rsa key and/or certificate files provided to sign the package
Checking if package descriptor file is present..
Skipping descriptor schema validation..
Created Staging directory at :  /tmp/303597821
Copying contents to staging directory
Creating an inner envelope for application artifacts
Including  rootfs.img
Generated  /tmp/303597821/artifacts.tar.gz
Calculating SHA1 checksum for package contents..
Parsing Package Metadata file :  /tmp/303597821/.package.metadata
Updated package metadata file :  /tmp/303597821/.package.metadata
Root Directory :  /tmp/303597821
Output file:  /tmp/324856888
Path:  .package.metadata
SHA1 : ac5ae7bae15fc5909fc949b0ade317868fe3f31c
Path:  artifacts.tar.gz
SHA1 : 96745dab8e4b150d010a744bdf71884699d2aee4
Path:  package.yaml
SHA1 : 980382157d6ef1af4912047a5bdeaf4c51d1f0cc
Generated package manifest at  package.mf
Generating IOx Package..
Package docker image iox-bottle at /root/iox/LXC/iox-bottle.tar
```

# Verify package created

```
fabri@ubuntu-148# ls -l iox-bottle.tar
-rw-r--r-- 1 root root 23177728 Apr 19 10:24 iox-bottle.tar
```
Copy package to Cisco IOS XE device in an external storage (bootflash is not supported for App Hosting)

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
