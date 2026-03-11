interfaces vlan-tags outer-tag inner-tag
----------------------------------------

**Minimum user role:** operator

To configure a sub-interface with QinQ encapsulation (802.1ad double-tagged VLAN):

**Command syntax: vlan-tags outer-tag [outer-vlan-id] inner-tag [inner-vlan-id]** outer-tpid [tpid]

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- Vlan-tags command is available only for sub-interface/bundle.sub-interface.

- Vlan-tags command is not available for physical/loopback interfaces.

- Vlan-tags is a must parameter for a QinQ sub-interface.

- Vlan-tags and vlan-id commands are mutually exclusive.

- Sub-interface is created when using the interface.sub-interface-id syntax.

- Vlan-tags command configures the sub-interface with QinQ encapsulation.

- To preserve sub-interface properties, it is possible to change its type from QinQ to VLAN without removing the sub-interface configuration.

- The default outer TPID value is 0x8100. Inner TPID value is always 0x8100.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter     | Description                                                                      | Range      | Default |
+===============+==================================================================================+============+=========+
| outer-vlan-id | The outer VLAN ID to assign to the sub-interface. The VLAN ID does not need to   | 1-4094     | \-      |
|               | match the sub-interface ID.                                                      |            |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+
| inner-vlan-id | The inner VLAN ID to assign to the sub-interface. The VLAN ID does not need to   | 1-4094     | \-      |
|               | match the sub-interface ID.                                                      |            |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+
| tpid          | The TPID to identify the protocol type of the outer VLAN tag.                    | | 0x8100   | 0x8100  |
|               |                                                                                  | | 0x88a8   |         |
|               |                                                                                  | | 0x9100   |         |
|               |                                                                                  | | 0x9200   |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.2
    dnRouter(cfg-if-bundle-1.2)# vlan-tags outer-tag 20 inner-tag 20

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.3
    dnRouter(cfg-if-bundle-1.3)# vlan-tags outer-tag 20 inner-tag 30

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.4
    dnRouter(cfg-if-bundle-1.4)# vlan-tags outer-tag 20 inner-tag 40

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge10-1/1/2.100
    dnRouter(cfg-if-ge10-1/1/2.100)# vlan-tags outer-tag 20 inner-tag 301 outer-tpid 0x8100


**Removing Configuration**

To remove the sub-interface configuration:
::

    dnRouter(cfg-if)# no bundle-1.2

::

    dnRouter(cfg-if)# no ge10-1/1/2.100

**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 16.1    | Command introduced                          |
+---------+---------------------------------------------+
| 17.1    | Added support for a configurable outer TPID |
+---------+---------------------------------------------+
