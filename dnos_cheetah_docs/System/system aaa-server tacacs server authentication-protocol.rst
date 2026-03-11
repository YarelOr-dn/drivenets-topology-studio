system aaa-server tacacs server priority address authentication-protocol
------------------------------------------------------------------------

**Minimum user role:** admin

To configure the authentication protocol to be used:

**Command syntax: authentication-protocol [authentication-protocol]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- Notice the change in prompt.

.. - 'no authentication-protocol' command sets default authentication-protocol value which is 'pap'


**Parameter table**

+-------------------------+------------------------------------------------------------+-----------+---------+
| Parameter               | Description                                                | Range     | Default |
+=========================+============================================================+===========+=========+
| authentication-protocol | Set the authentication protocol used by the TACACS server. | | pap     | pap     |
|                         |                                                            | | chap    |         |
|                         |                                                            | | ascii   |         |
+-------------------------+------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# authentication-protocol ascii


**Removing Configuration**

To revert the authentication protocol to the default value:
::

    dnRouter(cfg-aaa-tacacs-server)# no authentication-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
