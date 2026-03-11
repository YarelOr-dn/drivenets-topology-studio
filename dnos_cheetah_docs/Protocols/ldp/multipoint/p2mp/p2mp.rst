protocols ldp multipoint p2mp
-----------------------------

**Minimum user role:** operator

To configure the multipoint LDP point-to-multipoint capability, enter the mLDP P2MP configuration mode:

**Command syntax: p2mp**

**Command mode:** config

**Hierarchies**

- protocols ldp multipoint

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)# p2mp
    dnRouter(cfg-ldp-mldp-p2mp)#


**Removing Configuration**

To revert all mLDP P2MP parameters to their default values: 
::

    dnRouter(cfg-protocols-ldp-mldp)# no p2mp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
