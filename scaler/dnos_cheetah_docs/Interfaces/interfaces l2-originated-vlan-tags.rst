interfaces l2-originated-vlan-tags
----------------------------------

**Minimum user role:** operator

To configure the VLAN tags to be applied to locally generated traffic originating from a multi-VLAN sub-interface:

**Command syntax: l2-originated-vlan-tags**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**
- L2-originated-vlan-tags command is applicable only for L2 multi-VLAN sub-interfaces.

- If l2-originated-vlan-tags command is not configured, by default a multi-VLAN sub-interface will send locally generated traffic as untagged.

- VLAN tags of traffic forwarded through L2 multi-VLAN sub-interfaces are preserved as usual.

**Example**
::

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0.100
    dnRouter(cfg-if-ge100-0/0/0.100)# l2-originated-vlan-tags
    dnRouter(cfg-if-ge100-0/0/0.100-l2-originated-vlan-tags)#


**Removing Configuration**

To remove the l2-originated-vlan-tags configuration:
::

    dnRouter(cfg-if-ge100-0/0/0.100)# no l2-originated-vlan-tags

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
