interfaces dhcpv6 relay-agent admin-state
-----------------------------------------

**Minimum user role:** operator

To enable DHCPv6 relay agent on the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dhcpv6 relay-agent

**Note**

- At least one DHCP IPv6 server must be configured to enable the relay agent on the interface.

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
    dnRouter(cfg-if-ge100-0/0/0)# dhcpv6 relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcpv6-relay)# admin-state enabled


**Removing Configuration**

To return DHCPv6 relay agent admin-state on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcpv6-relay)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
