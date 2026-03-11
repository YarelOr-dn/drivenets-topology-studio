network-services vrf instance protocols bgp default local-preference
--------------------------------------------------------------------

**Minimum user role:** operator

Routers in the same AS exchange the local preference attribute in order to indicate to the AS which path is preferred for exiting the AS and reaching a specific network.

A path with a higher local preference is preferred more.

To configure the default local preference for advertised routes:

**Command syntax: default local-preference [default-local-preference]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Parameter table**

+--------------------------+-------------------------------------------+--------------+---------+
| Parameter                | Description                               | Range        | Default |
+==========================+===========================================+==============+=========+
| default-local-preference | Change the default local preference value | 0-4294967295 | 100     |
+--------------------------+-------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# default local-preference 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-bgp)# no default local-preference

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
