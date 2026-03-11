interfaces ndp host-address mac-address
---------------------------------------

**Minimum user role:** operator

For static routing, you need to manually specify the next hop router's address using the link-local address of the router.

To add a static NDP entry for an interface, use the following command in configuration mode:

**Command syntax: ndp host-address [host-ipv6-address] mac-address [mac-address]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan
  - IRB

**Parameter table**

+-------------------+------------------------------------------------------------------+-------------------+---------+
| Parameter         | Description                                                      | Range             | Default |
+===================+==================================================================+===================+=========+
| host-ipv6-address | The IPv6 address of the host device being added to the NDP table | X:X::X:X          | \-      |
+-------------------+------------------------------------------------------------------+-------------------+---------+
| mac-address       | The MAC address for the host device being added to the NDP table | xx:xx:xx:xx:xx:xx | \-      |
+-------------------+------------------------------------------------------------------+-------------------+---------+

**Example**

To add a static NDP entry that maps 2001:ab12::1 to MAC address 12:ab:47:dd:ff:89:
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ndp host-address 2001:ab12::1 mac-address 12:ab:47:dd:ff:89


**Removing Configuration**

To remove a specific static NDP entry:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ndp host-address 2001:ab12::1

To clear all static NDP entries on the interface:
::

    dnRouter(cfg-if-ge10-1/1/1)# no ndp

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces, applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 11.0    | Changed syntax from ipv6-address to host-address                   |
+---------+--------------------------------------------------------------------+
