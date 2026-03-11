forwarding-options preferred-vlan-ranges outer-vlan-ranges
----------------------------------------------------------

**Minimum user role:** operator

To configure the preferred outer VLAN ranges that can be reused in the system without wasting additional resources:

**Command syntax: outer-vlan-ranges [preferred-vlan-range]**

**Command mode:** config

**Hierarchies**

- forwarding-options preferred-vlan-ranges

**Note**

- Up to 5 preferred outer VLAN ranges can be configured.

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter            | Description                                                                      | Range | Default |
+======================+==================================================================================+=======+=========+
| preferred-vlan-range | Preferred outer VLAN ranges. These ranges may be re-used in the system without   | \-    | \-      |
|                      | wasting additional resources.                                                    |       |         |
+----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# preferred-vlan-ranges
    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# outer-vlan-ranges 100-200
    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# outer-vlan-ranges 400-410, 500-555, 1000-1200


**Removing Configuration**

To remove a specific preferred outer VLAN range:
::

    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# no outer-vlan-ranges 400-410

To remove all preferred outer VLAN ranges:
::

    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# no outer-vlan-ranges

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
