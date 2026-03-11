interfaces mac-address
----------------------

**Minimum user role:** operator

To switch frames between LAN ports efficiently, an address table is maintained. When the NCR receives a frame, it associates the media access control (MAC) address of the sending network device with the LAN port on which it was received. When it receives a frame for a MAC destination address not listed in its address table, it floods the frame to all LAN ports of the same VLAN except the port that received the frame. When the destination station replies, its MAC address is added to the address table from the source address of the reply.

You can enter a new (static) MAC address for physical or LAG interfaces only. This will replace the default MAC address.

To change MAC address of a physical or LAG interface, use the following command in configuration mode:

**Command syntax: mac-address [mac-address]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Bundle
  - IRB

- For a bundle interface, the default value is the mac address of the first member. The MAC address is taken from DriveNets' pool (OUI 84:40:76:XX:XX:XX), where the last 3 bytes are randomized.

- When configuring a bundle interface without configuring a specific mac-address for it, "no mac-address" will not do anything because it has selected the "default" value of the bundle interface.

**Parameter table**

+-------------+-----------------------------------+-------------------+---------+
| Parameter   | Description                       | Range             | Default |
+=============+===================================+===================+=========+
| mac-address | The MAC address for the interface | xx:xx:xx:xx:xx:xx | \-      |
+-------------+-----------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# mac-address 10:22:33:44:55:00

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# mac-address 00:00:00:00:00:01


**Removing Configuration**

To revert to the default MAC address (that of the connected device):
::

    dnRouter(cfg-if-ge100-1/1/1)# no mac-address

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 9.0     | Not supported in this version.                                     |
+---------+--------------------------------------------------------------------+
| 10.0    | Command re-introduced                                              |
+---------+--------------------------------------------------------------------+
| 16.2    | Management bond interfaces removed                                 |
+---------+--------------------------------------------------------------------+
