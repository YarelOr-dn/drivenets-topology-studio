system ssh server vrf client-list type
--------------------------------------

**Minimum user role:** operator

Defines whether the listed clients will be granted access to the in-band SSH server. 

**Command syntax: client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- system ssh server vrf

**Note**

- If the list-type is set to "allow", the client list must not be empty.

- no command return the list type to its default value

- if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+-----------+-----------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                 | Range     | Default |
+===========+=============================================================================+===========+=========+
| list-type | Configure black or white list type of incoming IP-addresses for SSH service | | allow   | deny    |
|           |                                                                             | | deny    |         |
+-----------+-----------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server vrf default
    dnRouter(cfg-ssh-server-vrf)# client-list type allow


**Removing Configuration**

To revert the type to default:
::

    dnRouter(cfg-ssh-server-vrf)# no client-list type

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 6.0     | Command introduced            |
+---------+-------------------------------+
| 10.0    | Merged with system ssh server |
+---------+-------------------------------+
| 11.0    | Moved into system ssh server  |
+---------+-------------------------------+
| 13.1    | Moved under VRF hierarchy     |
+---------+-------------------------------+
