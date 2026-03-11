system ntp server vrf key
-------------------------

**Minimum user role:** operator

To configure an NTP server key:

**Command syntax: key [key]**

**Command mode:** config

**Hierarchies**

- system ntp server vrf

**Parameter table**

+-----------+----------------+---------+---------+
| Parameter | Description    | Range   | Default |
+===========+================+=========+=========+
| key       | Encryption key | 1-65533 | \-      |
+-----------+----------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 12.12.12.12 vrf default
    dnRouter(cfg-system-ntp-server)# key 12344


**Removing Configuration**

To remove the specified NTP server prefer:
::

    dnRouter(cfg-system-ntp-server)# no key

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
