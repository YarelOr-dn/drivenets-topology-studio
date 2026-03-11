protocols ldp multipoint
------------------------

**Minimum user role:** operator

To configure multipoint LDP, enter the mLDP configuration mode:

**Command syntax: multipoint**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)#


**Removing Configuration**

To revert all mLDP parameters to their default values: 
::

    dnRouter(cfg-protocols-ldp)# no multipoint

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
