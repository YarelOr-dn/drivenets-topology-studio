interfaces vlan-id list
-----------------------

**Minimum user role:** operator

VLANs are mandatory on sub-interfaces and virtual-l2-interfaces. Therefore, you can only change the VLAN on existing interfaces, but not remove them altogether.

**Command syntax: vlan-id list [vlan-id-list]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is available for sub-interface (geX-<f>/<n>/<p>.subinterface) and is mandatory.

- The command is available for bundle.sub-interface (bundle-<bundle id>.subinterface) and is mandatory.

- The command is available for virtual-l2-interface (nat-X/ipsec-X) and is mandatory.

- The command is not available for loopback interfaces.

- vlan-tags and vlan-id are mutually exclusive.

- VLAN lists and ranges are only applicable for L2-service enabled sub-interfaces.

- Sub-interfaces with VLAN lists do not require a TPID. By default the VLAN translation action is to preserve incoming packet's VLAN headers. Locally generated traffic will be sent as untagged.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter    | Description                                                                      | Range  | Default |
+==============+==================================================================================+========+=========+
| vlan-id-list | The list of VLAN IDs to assign to the sub-interface (can be specified as         | 1-4094 | \-      |
|              | specific values and ranges, separated by commas). The VLAN IDs do not need to    |        |         |
|              | match the sub-interface ID.                                                      |        |         |
+--------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-2.300
    dnRouter(cfg-if-bundle-2.300)# vlan-id list 300
    dnRouter(cfg-if-bundle-2.300)# vlan-id list 350, 360, 400-410, 510-520


**Removing Configuration**

To remove the sub-interface configuration:
::

    dnRouter(cfg-if)# no bundle-1.1

::

    dnRouter(cfg-if)# no bundle-1.200

::

    dnRouter(cfg-if)# no ge10-1/1/1.100

::

    dnRouter(cfg-if)# no nat-0

::

    dnRouter(cfg-if)# no ipsec-0

To remove specific VLAN ID from the list:
::

    dnRouter(cfg-if-ge100-0/0/0.2)# no vlan-id list 100

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
