interfaces vlan-manipulation egress-mapping action preserve-preserve
--------------------------------------------------------------------

**Minimum user role:** operator

To configure the VLAN manipulation egress mapping for the preserve-preserve action:

**Command syntax: vlan-manipulation egress-mapping action preserve-preserve**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is supported for L2 inband network interfaces (single-tagged, double-tagged, port-mode) attached to any L2 service type

- The PCP policy is determined according to the QoS policy configuration.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.1
    dnRouter(cfg-if-bundle-1.1)# vlan-manipulation egress-mapping action preserve-preserve


**Removing Configuration**

To remove VLAN manipulation egress mapping configuration:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no vlan-manipulation egress-mapping

To remove VLAN manipulation configuration altogether:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no vlan-manipulation

**Command History**

+---------+------------------------------+
| Release | Modification                 |
+=========+==============================+
| 18.3    | Command introduced           |
+---------+------------------------------+
| 19.1    | Removed PCP policy parameter |
+---------+------------------------------+
