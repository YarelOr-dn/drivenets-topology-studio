forwarding-options preferred-vlan-ranges inner-vlan-ranges
----------------------------------------------------------

**Minimum user role:** operator

To configure the preferred inner VLAN ranges that can be reused in the system without wasting additional resources:

**Command syntax: inner-vlan-ranges [preferred-vlan-range]**

**Command mode:** config

**Hierarchies**

- forwarding-options preferred-vlan-ranges

**Note**

- Up to 5 preferred inner VLAN ranges can be configured (the inner tag of the two outermost tags).

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter            | Description                                                                      | Range | Default |
+======================+==================================================================================+=======+=========+
| preferred-vlan-range | Preferred inner VLAN ranges. These ranges may be re-used in the system without   | \-    | \-      |
|                      | wasting additional resources.                                                    |       |         |
+----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# preferred-vlan-ranges
    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# inner-vlan-ranges 100-200
    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# inner-vlan-ranges 400-410, 500-555, 1000-1200


**Removing Configuration**

To remove a specific preferred inner VLAN range:
::

    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# no inner-vlan-ranges 400-410

To remove all preferred inner VLAN ranges:
::

    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)# no inner-vlan-ranges

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
