interfaces l2-originated-vlan-tags inner-tag
--------------------------------------------

**Minimum user role:** operator

To configure the inner VLAN tag to be applied to locally generated traffic originating from a multi-VLAN sub-interface:

**Command syntax: inner-tag [l2-originated-inner-vlan-id]** inner-tpid [l2-originated-inner-tpid]

**Command mode:** config

**Hierarchies**

- interfaces l2-originated-vlan-tags

**Note**
- L2-originated-vlan-tags command is applicable only for L2 multi-VLAN sub-interfaces.

- If l2-originated-vlan-tags command is not configured, by default a multi-VLAN sub-interface will send locally generated traffic as untagged.

- VLAN tags of traffic forwarded through L2 multi-VLAN sub-interfaces are preserved as usual.

**Parameter table**

+-----------------------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter                   | Description                                                                      | Range      | Default |
+=============================+==================================================================================+============+=========+
| l2-originated-inner-vlan-id | The inner VLAN ID to assign to locally originated traffic over the multi-VLAN    | 1-4094     | \-      |
|                             | sub-interface. The VLAN ID does not need to match the sub-interface ID.          |            |         |
+-----------------------------+----------------------------------------------------------------------------------+------------+---------+
| l2-originated-inner-tpid    | The TPID to identify the protocol type of the inner VLAN tag.                    | | 0x8100   | 0x8100  |
|                             |                                                                                  | | 0x88a8   |         |
|                             |                                                                                  | | 0x9100   |         |
|                             |                                                                                  | | 0x9200   |         |
+-----------------------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0.100
    dnRouter(cfg-if-ge100-0/0/0.100)# l2-originated-vlan-tags
    dnRouter(cfg-if-ge100-0/0/0.100-l2-originated-vlan-tags)# inner-tag 350 inner-tpid 0x9100


**Removing Configuration**

To remove the inner VLAN tag configuration:
::

    dnRouter(cfg-if-ge100-0/0/0.100-l2-originated-vlan-tags)# no inner-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
