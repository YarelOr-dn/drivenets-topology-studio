interfaces vlan-manipulation ingress-mapping action pop-pop
-----------------------------------------------------------

**Minimum user role:** operator

To configure the VLAN manipulation ingress mapping for a pop-pop action:

**Command syntax: vlan-manipulation ingress-mapping action pop-pop**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is supported for L2 inband network interfaces (single-tagged, double-tagged, port-mode) attached to any L2 service type.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.1
    dnRouter(cfg-if-bundle-1.1)# vlan-manipulation ingress-mapping action pop-pop


**Removing Configuration**

To remove VLAN manipulation ingress mapping configuration:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no vlan-manipulation ingress-mapping

To remove VLAN manipulation configuration altogether:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no vlan-manipulation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
