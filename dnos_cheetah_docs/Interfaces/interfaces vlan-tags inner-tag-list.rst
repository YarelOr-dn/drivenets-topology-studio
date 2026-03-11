interfaces vlan-tags outer-tag inner-tag-list
---------------------------------------------

**Minimum user role:** operator

To configure a sub-interface with QinQ encapsulation (802.1ad double-tagged VLAN) with a list of inner VLAN tags:

**Command syntax: vlan-tags outer-tag [outer-vlan-id] inner-tag-list [inner-vlan-id-list]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The vlan-tags command is available only for sub-interface/bundle.sub-interface.

- The vlan-tags command is not available for physical/loopback interfaces.

- Vlan-tags is a must parameter for a QinQ sub-interface.

- Vlan-tags and vlan-id commands are mutually exclusive.

- A sub-interface is created when using the interface.sub-interface-id syntax.

- Vlan-tags command configures the sub-interface with QinQ encapsulation.

- To preserve the sub-interface properties, it is possible to change its type from QinQ to VLAN without removing the sub-interface configuration.

- VLAN lists and ranges are only applicable for L2-service enabled sub-interfaces.

- Sub-interfaces with VLAN lists do not require TPID. By default VLAN translation action is to preserve incoming packet's VLAN headers. Locally generated traffic will be sent as untagged.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter          | Description                                                                      | Range  | Default |
+====================+==================================================================================+========+=========+
| outer-vlan-id      | The outer VLAN ID to assign to the sub-interface. The VLAN ID does not need to   | 1-4094 | \-      |
|                    | match the sub-interface ID.                                                      |        |         |
+--------------------+----------------------------------------------------------------------------------+--------+---------+
| inner-vlan-id-list | The list of VLAN IDs to assign to the sub-interface (can be specified as         | 1-4094 | \-      |
|                    | sepcific values and ranges, separated by commas). The VLAN IDs do not need to    |        |         |
|                    | match the sub-interface ID.                                                      |        |         |
+--------------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge10-1/1/2.100
    dnRouter(cfg-if-ge10-1/1/2.100)# vlan-tags outer-tag 100 inner-tag-list 301, 304, 305-310, 400-500


**Removing Configuration**

To remove the sub-interface configuration:
::

    dnRouter(cfg-if)# no bundle-1.2

::

    dnRouter(cfg-if)# no ge10-1/1/2.100

To remove specific VLAN tag from the inner VLAN list:
::

    dnRouter(cfg-if-ge100-0/0/0.2)# no vlan-tags outer-tag 100 inner-tag-list 301

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
