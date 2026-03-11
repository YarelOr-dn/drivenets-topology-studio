protocols ldp multipoint load-split
-----------------------------------

**Minimum user role:** operator

To configure multipoint LDP load split, enter the mLDP load split configuration mode:

**Command syntax: load-split**

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
    dnRouter(cfg-protocols-ldp-mldp)# load-split
    dnRouter(cfg-ldp-mldp-ls)#


**Removing Configuration**

To revert all mLDP load split parameters to their default values: 
::

    dnRouter(cfg-protocols-ldp-mldp)# no load-split

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
