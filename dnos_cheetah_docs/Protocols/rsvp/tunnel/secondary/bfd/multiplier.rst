protocols rsvp tunnel secondary bfd multiplier
----------------------------------------------

**Minimum user role:** operator

The multiplier defines the number of min-rx intervals in which a BFD packet is not received before the BFD session goes down.

To configure a local BFD multiplier:


**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary bfd

**Parameter table**

+------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                                      | Range | Default |
+============+==================================================================================+=======+=========+
| multiplier | The number of min-rx intervals in which no BFD packet is received as expected    | 2-16  | 3       |
|            | (or the number of missing BFD packets) before the BFD session goes down.         |       |         |
+------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# bfd
    dnRouter(cfg-tunnel-secondary-bfd)# multiplier 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-tunnel-secondary-bfd)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
