system ntp server vrf
---------------------

**Minimum user role:** operator

To configure an NTP server:

**Command syntax: server [address] vrf [vrf]**

**Command mode:** config

**Hierarchies**

- system ntp

**Parameter table**

+-----------+---------------------+------------------+---------+
| Parameter | Description         | Range            | Default |
+===========+=====================+==================+=========+
| address   | NTP server config   | | A.B.C.D        | \-      |
|           |                     | | X:X::X:X       |         |
+-----------+---------------------+------------------+---------+
| vrf       | The name of the vrf | | string         | \-      |
|           |                     | | length 1-255   |         |
+-----------+---------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 12.12.12.12 vrf default


**Removing Configuration**

To remove the specified NTP server:
::

    dnRouter(cfg-system-ntp)# no server 12.12.12.12 vrf default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
