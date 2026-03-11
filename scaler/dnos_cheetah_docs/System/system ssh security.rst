system ssh security
-------------------

**Minimum user role:** operator

Configure SSH security parameters:

**Command syntax: security**

**Command mode:** config

**Hierarchies**

- system ssh

**Note**

- Security affects both SSH Server and Netconf servers on all vrfs

- Security does not affect SSH Client

- Notice the change in prompt.

- no commands removes configuration/set the default value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# security
    dnRouter(cfg-ssh-server-security)# mac hmac-sha2-512
    dnRouter(cfg-ssh-server-security)# !
    dnRouter(cfg-ssh-server)# security ciphers chacha20-poly1305-openssh.com,aes256-gcm-openssh.com


**Removing Configuration**

To revert to default algorithms
::

    dnRouter(cfg-system-ssh)# no security

**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| TBD     | Command introduced as part of new hierarchy |
+---------+---------------------------------------------+
