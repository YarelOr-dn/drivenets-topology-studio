interfaces vlan-manipulation egress-mapping action swap-swap outer-tag outer-tpid inner-tag inner-tpid
------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the VLAN manipulation egress mapping for a swap-swap action:

**Command syntax: vlan-manipulation egress-mapping action swap-swap outer-tag [vlan-id-outer] outer-tpid [tpid-outer] inner-tag [vlan-id-inner] inner-tpid [tpid-inner]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is supported for L2 inband network interfaces (single-tagged, double-tagged, port-mode) attached to any L2 service type.

- The PCP policy is determined according to the QoS policy configuration.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter     | Description                                                                      | Range      | Default |
+===============+==================================================================================+============+=========+
| vlan-id-outer | Optionally specifies a fixed VLAN identifier that is used by the action          | 1-4094     | \-      |
|               | configured in 'vlan-stack-action'. For example, if the action is 'POP' then a    |            |         |
|               | VLAN identifier is removed from the stack but the value of this leaf is used     |            |         |
|               | instead. This value must be non-zero if the 'vlan-stack-action' is one of 'PUSH' |            |         |
|               | or 'SWAP'. The outer VLAN identifier is also applicable to single tagged         |            |         |
|               | actions.                                                                         |            |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+
| tpid-outer    | Optionally override the tag protocol identifier field (TPID) that is used by the | | 0x8100   | \-      |
|               | action configured by 'vlan-stack-action' when modifying the VLAN stack. The      | | 0x9100   |         |
|               | outer TPID is also applicable to single tagged actions.                          | | 0x9200   |         |
|               |                                                                                  | | 0x88a8   |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+
| vlan-id-inner | Optionally specifies a fixed VLAN identifier that is used by the action          | 1-4094     | \-      |
|               | configured in 'vlan-stack-action'. For example, if the action is 'POP' then a    |            |         |
|               | VLAN identifier is removed from the stack but the value of this leaf is used     |            |         |
|               | instead. This value must be non-zero if the 'vlan-stack-action' is one of 'PUSH' |            |         |
|               | or 'SWAP'.                                                                       |            |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+
| tpid-inner    | Optionally override the tag protocol identifier field (TPID) that is used by the | | 0x8100   | \-      |
|               | action configured by 'vlan-stack-action' when modifying the VLAN stack.          | | 0x9100   |         |
|               |                                                                                  | | 0x9200   |         |
|               |                                                                                  | | 0x88a8   |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.1
    dnRouter(cfg-if-bundle-1.1)# vlan-manipulation egress-mapping action swap-swap outer-tag 100 outer-tpid 0x88a8 inner-tag 200 inner-tpid 0x8100


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
| 18.2    | Command introduced           |
+---------+------------------------------+
| 19.1    | Removed PCP policy parameter |
+---------+------------------------------+
