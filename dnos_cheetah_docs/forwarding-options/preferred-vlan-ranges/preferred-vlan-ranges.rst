forwarding-options preferred-vlan-ranges
----------------------------------------

**Minimum user role:** operator

To enter the preferred VLAN ranges configuration level:

**Command syntax: preferred-vlan-ranges**

**Command mode:** config

**Hierarchies**

- forwarding-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# preferred-vlan-ranges
    dnRouter(cfg-fwd_opts-preferred-vlan-ranges)#


**Removing Configuration**

To remove all the configured preferred VLAN ranges:
::

    dnRouter(cfg-fwd_opts)# no preferred-vlan-ranges

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
