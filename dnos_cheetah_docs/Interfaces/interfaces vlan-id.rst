interfaces vlan-id
------------------

**Minimum user role:** operator

VLANs are mandatory on sub-interfaces and virtual-l2-interfaces. Therefore, you can only change the VLAN on existing ones, but not remove them altogether.

**Command syntax: vlan-id [vlan-id]** tpid [tpid]

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is available for sub-interface (geX-<f>/<n>/<p>.subinterface) and is mandatory.

- The command is available for bundle.sub-interface (bundle-<bundle id>.subinterface) and is mandatory.

- The command is available for virtual-l2-interface (nat-X/ipsec-X) and is mandatory.

- The command is not available for loopback interfaces.

- vlan-tags and vlan-id are mutually exclusive.

- VLAN lists and ranges are only applicable for L2-service enabled sub-interfaces

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| vlan-id   | The VLAN ID to assign to the sub-interface. The VLAN ID does not need to match   | 1-4094     | \-      |
|           | the sub-interface ID.                                                            |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+
| tpid      | The TPID to identify the protocol type of the VLAN tag.                          | | 0x8100   | 0x8100  |
|           |                                                                                  | | 0x9100   |         |
|           |                                                                                  | | 0x9200   |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.1
    dnRouter(cfg-if-bundle-1.1)# vlan-id 20

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.200
    dnRouter(cfg-if-bundle-1.200)# vlan-id 200

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge10-1/1/1.100
    dnRouter(cfg-if-ge10-1/1/1.100)# vlan-id 301 tpid 0x9100

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# nat-0
    dnRouter(cfg-if-nat-0)# vlan-id 1337

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ipsec-0
    dnRouter(cfg-if-ipsec-0)# vlan-id 1234


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

**Command History**

+----------+--------------------------------------------------------------------+
| Release  | Modification                                                       |
+==========+====================================================================+
| 5.1      | Command introduced                                                 |
+----------+--------------------------------------------------------------------+
| 6.0      | Changed syntax from interface to interfaces; applied new hierarchy |
+----------+--------------------------------------------------------------------+
| 17.1     | Added support for a configurable TPID                              |
+----------+--------------------------------------------------------------------+
| 18.0.11  | Added support for virtual L2 interfaces (nat, ipsec)               |
+----------+--------------------------------------------------------------------+
