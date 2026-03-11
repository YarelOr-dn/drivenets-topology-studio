interfaces arp host-address mac-address
---------------------------------------

**Minimum user role:** operator

You can add static entries to the ARP table. Static entries are permanent (unless they are manually removed) and take precedence over dynamic updates. To add a static ARP entry, use the following command in configuration mode:

**Command syntax: arp host-address [host-ipv4-address] mac-address [mac-address]**

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

- Gratuitous ARP is supported by default on all interfaces.

- Dynamic ARP entries remain in the ARP cache for 60 seconds.

- The command is not available to loopback interface.

- The host-ipv4-address is always a /32 ipv4-address.

**Parameter table**

+-------------------+------------------------------------------------------------------+-------------------+---------+
| Parameter         | Description                                                      | Range             | Default |
+===================+==================================================================+===================+=========+
| host-ipv4-address | The IPv4 address of the host device being added to the ARP table | A.B.C.D           | \-      |
+-------------------+------------------------------------------------------------------+-------------------+---------+
| mac-address       | The MAC address for the host device being added to the ARP table | xx:xx:xx:xx:xx:xx | \-      |
+-------------------+------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# arp host-address 1.2.3.4 mac-address ab:ab:ab:ab:ab:ab

    dnRouter(cfg-if)# ge100-1/1/2
    dnRouter(cfg-if-ge100-1/1/2)# arp host-address 1.2.3.5 mac-address ab:ab:ab:ab:ab:ab

    dnRouter(cfg-if)# ge100-1/1/1.100
    dnRouter(cfg-if-ge100-1/1/1.100)# arp host-address 10.100.10.1 mac-address ab:ab:ab:ab:ab:ab

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# arp host-address 10.100.10.1 mac-address ab:ab:ab:ab:ab:ab

    dnRouter(cfg-if)# bundle-1.100
    dnRouter(cfg-if-bundle-1.100)# arp host-address 20.20.20.2 mac-address ab:ab:ab:ab:ab:ab


**Removing Configuration**

To remove a static ARP entry for the interface:
::

    dnRouter(cfg-if-ge10-1/1/1)# no arp

To remove a static ARP entry for a specific ipv4-address:
::

    dnRouter(cfg-if-ge100-1/1/1)# no arp host-address 1.2.3.5

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces, applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 11.0    | Changed syntax from ipv4-address to host-address                   |
+---------+--------------------------------------------------------------------+
