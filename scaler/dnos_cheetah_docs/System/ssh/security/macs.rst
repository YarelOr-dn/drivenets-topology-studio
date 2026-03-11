system ssh security macs
------------------------

**Minimum user role:** operator

Configure SSH Server and Netconf MAC algorithms. SSH Client is not affected

**Command syntax: macs [macs]** [, macs, macs]

**Command mode:** config

**Hierarchies**

- system ssh security

**Parameter table**

+-----------+----------------------------------------------------------------+-----------------------------------+---------+
| Parameter | Description                                                    | Range                             | Default |
+===========+================================================================+===================================+=========+
| macs      | List of available MAC (message authentication code) algorithms | | hmac-sha1                       | \-      |
|           |                                                                | | hmac-sha1-96                    |         |
|           |                                                                | | hmac-sha2-256                   |         |
|           |                                                                | | hmac-sha2-512                   |         |
|           |                                                                | | hmac-md5                        |         |
|           |                                                                | | hmac-md5-96                     |         |
|           |                                                                | | umac-64-openssh.com             |         |
|           |                                                                | | umac-128-openssh.com            |         |
|           |                                                                | | hmac-sha1-etm-openssh.com       |         |
|           |                                                                | | hmac-sha1-96-etm-openssh.com    |         |
|           |                                                                | | hmac-sha2-256-etm-openssh.com   |         |
|           |                                                                | | hmac-sha2-512-etm-openssh.com   |         |
|           |                                                                | | hmac-md5-etm-openssh.com        |         |
|           |                                                                | | hmac-md5-96-etm-openssh.com     |         |
|           |                                                                | | umac-64-etm-openssh.com         |         |
|           |                                                                | | umac-128-etm-openssh.com        |         |
+-----------+----------------------------------------------------------------+-----------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# security
    dnRouter(cfg-system-ssh-security)# macs hmac-sha2-512


**Removing Configuration**

To revert the ssh security macs to default: 
::

    dnRouter(cfg-system-ssh-security)# no macs

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
