interfaces dhcpv6 relay-agent
-----------------------------

**Minimum user role:** operator

To enter IPv6 DHCP relay agent configuration mode:

**Command syntax: dhcpv6 relay-agent**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan
  - IRB

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcpv6 relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcpv6-relay)#


**Removing Configuration**

To remove the DHCP relay agent configuration:
::

    dnRouter(cfg-if-ge100-0/0/0)# no dhcp relay-agent

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
