protocols rsvp auto-bypass optimization
---------------------------------------

**Minimum user role:** operator

Enable ldp sync for all tunnels set with ldp-tunneling. When enabled, rsvp tunnel is excluded to be used for ldp tunneling, by either shortcut of forwarding-adjecency, if targeted LDP peer is missing.

**Command syntax: optimization [optimization]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass

**Parameter table**

+--------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter    | Description                                                                      | Range        | Default |
+==============+==================================================================================+==============+=========+
| optimization | Run sequential path calculations for tunnels in UP state to find an optimized    | | enabled    | \-      |
|              | path                                                                             | | disabled   |         |
+--------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# optimization enabled


**Removing Configuration**

To return the optimization to the default:
::

    dnRouter(cfg-protocols-rsvp)# no optimization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
