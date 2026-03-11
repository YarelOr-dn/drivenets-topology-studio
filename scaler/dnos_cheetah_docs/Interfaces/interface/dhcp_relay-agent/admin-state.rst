interfaces dhcp relay-agent admin-state
---------------------------------------

**Minimum user role:** operator

To enable DHCP relay agent on the interface.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent

**Note**

- At least one DHCP server must be configured for enabling the relay agent on the interface.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enables the relay agent on the referenced interface. At least one server address | | enabled    | disabled |
|             | should also be configured for forwarding requests                                | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# admin-state enabled


**Removing Configuration**

To return DHCP relay agent admin-state on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
