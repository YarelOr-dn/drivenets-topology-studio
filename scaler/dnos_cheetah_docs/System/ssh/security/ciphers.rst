system ssh security ciphers
---------------------------

**Minimum user role:** operator

Configure SSH Server and Netconf Cipher algorithms. SSH Client is not affected

**Command syntax: ciphers [ciphers]** [, ciphers, ciphers]

**Command mode:** config

**Hierarchies**

- system ssh security

**Parameter table**

+-----------+-------------------------+-----------------------------------+---------+
| Parameter | Description             | Range                             | Default |
+===========+=========================+===================================+=========+
| ciphers   | List of allowed ciphers | | 3des-cbc                        | \-      |
|           |                         | | aes128-cbc                      |         |
|           |                         | | aes192-cbc                      |         |
|           |                         | | aes256-cbc                      |         |
|           |                         | | aes128-ctr                      |         |
|           |                         | | aes192-ctr                      |         |
|           |                         | | aes256-ctr                      |         |
|           |                         | | aes128-gcm-openssh.com          |         |
|           |                         | | aes256-gcm-openssh.com          |         |
|           |                         | | chacha20-poly1305-openssh.com   |         |
+-----------+-------------------------+-----------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# security
    dnRouter(cfg-system-ssh-security)# ciphers chacha20-poly1305-openssh.com,aes256-gcm-openssh.com


**Removing Configuration**

To revert the ssh server ciphers to default: 
::

    dnRouter(cfg-system-ssh-security)# no ciphers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
