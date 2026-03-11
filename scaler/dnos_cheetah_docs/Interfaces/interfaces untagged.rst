interfaces untagged
-------------------

**Minimum user role:** operator

The untagged command is available only for l2-service enabled sub-interfaces. Defining either VLANs or untagged is mandatory on sub-interfaces and virtual-l2-interfaces. Therefore, for l2-service enabled sub-interfaces, you can either set untagged or ensure that either vlan-id or vlan-tags are defined.

**Command syntax: untagged**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is available for sub-interface (geX-<f>/<n>/<p>.subinterface) when l2-service is enabled.

- The command is available for bundle.sub-interface (bundle-<bundle id>.subinterface) when l2-service is enabled.

- The command is not available for virtual-l2-interface (nat-X/ipsec-X).

- The command is not available for loopback interfaces.

- vlan-tags and vlan-id and untagged are all mutually exclusive.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1.1
    dnRouter(cfg-if-bundle-1.1)# l2-service enabled
    dnRouter(cfg-if-bundle-1.1)# untagged

    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge10-1/1/1.100
    dnRouter(cfg-if-ge10-1/1/1.100)# l2-service enabled
    dnRouter(cfg-if-ge10-1/1/1.100)# untagged


**Removing Configuration**

To remove the untagged configuration:
::

    dnRouter(cfg-if)# no untagged

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
