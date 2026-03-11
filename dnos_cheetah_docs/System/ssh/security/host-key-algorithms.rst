system ssh security host-key-algorithms
---------------------------------------

**Minimum user role:** operator

Configure SSH Server and Netconf Host-Key algorithms. SSH Client is not affected

**Command syntax: host-key-algorithms [host-key-algorithms]** [, host-key-algorithms, host-key-algorithms]

**Command mode:** config

**Hierarchies**

- system ssh security

**Parameter table**

+---------------------+-----------------------------------------------------------+-------------------------------------------------+---------+
| Parameter           | Description                                               | Range                                           | Default |
+=====================+===========================================================+=================================================+=========+
| host-key-algorithms | List host key signature algorithms that the server offers | | ssh-ed25519                                   | \-      |
|                     |                                                           | | ssh-ed25519-cert-v01-openssh.com              |         |
|                     |                                                           | | sk-ssh-ed25519-openssh.com                    |         |
|                     |                                                           | | sk-ssh-ed25519-cert-v01-openssh.com           |         |
|                     |                                                           | | ssh-rsa                                       |         |
|                     |                                                           | | rsa-sha2-256                                  |         |
|                     |                                                           | | rsa-sha2-512                                  |         |
|                     |                                                           | | ssh-dss                                       |         |
|                     |                                                           | | ecdsa-sha2-nistp256                           |         |
|                     |                                                           | | ecdsa-sha2-nistp384                           |         |
|                     |                                                           | | ecdsa-sha2-nistp521                           |         |
|                     |                                                           | | sk-ecdsa-sha2-nistp256-openssh.com            |         |
|                     |                                                           | | webauthn-sk-ecdsa-sha2-nistp256-openssh.com   |         |
|                     |                                                           | | ssh-rsa-cert-v01-openssh.com                  |         |
|                     |                                                           | | rsa-sha2-256-cert-v01-openssh.com             |         |
|                     |                                                           | | rsa-sha2-512-cert-v01-openssh.com             |         |
|                     |                                                           | | ssh-dss-cert-v01-openssh.com                  |         |
|                     |                                                           | | ecdsa-sha2-nistp256-cert-v01-openssh.com      |         |
|                     |                                                           | | ecdsa-sha2-nistp384-cert-v01-openssh.com      |         |
|                     |                                                           | | ecdsa-sha2-nistp521-cert-v01-openssh.com      |         |
|                     |                                                           | | sk-ecdsa-sha2-nistp256-cert-v01-openssh.com   |         |
+---------------------+-----------------------------------------------------------+-------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# security
    dnRouter(cfg-system-ssh-security)# host-key-algorithms ssh-ed25519,rsa-sha2-512


**Removing Configuration**

To revert the ssh server host-key-algorithms to default: 
::

    dnRouter(cfg-system-security)# no host-key-algorithms

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
