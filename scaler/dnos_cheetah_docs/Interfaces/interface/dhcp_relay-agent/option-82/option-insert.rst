interfaces dhcp relay-agent option-82 option-insert
---------------------------------------------------

**Minimum user role:** operator

To enable the DHCP Relay Agent Information Option (option 82) on the interface:

**Command syntax: option-insert [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Parameter table**

+-------------+-------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                             | Range        | Default  |
+=============+=========================================================================+==============+==========+
| admin-state | Enable sending the DHCP option for Relay Agent information -- option 82 | | enabled    | disabled |
|             |                                                                         | | disabled   |          |
+-------------+-------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# option-insert enabled


**Removing Configuration**

To return DHCP relay agent information option admin-state on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no option-insert

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
