interfaces dhcp relay-agent option-82 check-reply
-------------------------------------------------

**Minimum user role:** operator

To enforce validation of the DHCP Relay Agent Information Option (option 82) on the interface:

**Command syntax: check-reply [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Parameter table**

+-------------+---------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                         | Range        | Default  |
+=============+=====================================================================+==============+==========+
| admin-state | Enable validation of option 82 in replies received from DHCP server | | enabled    | disabled |
|             |                                                                     | | disabled   |          |
+-------------+---------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# check-reply enabled


**Removing Configuration**

To return DHCP relay agent information option check-reply configuration on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no check-reply

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
