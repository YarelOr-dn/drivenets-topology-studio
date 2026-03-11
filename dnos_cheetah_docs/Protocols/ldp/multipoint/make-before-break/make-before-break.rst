protocols ldp multipoint make-before-break
------------------------------------------

**Minimum user role:** operator

To configure the multipoint LDP make-before-break capability, enter the mLDP MBB configuration mode:

**Command syntax: make-before-break**

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
    dnRouter(cfg-protocols-ldp-mldp)# make-before-break
    dnRouter(cfg-ldp-mldp-mbb)#


**Removing Configuration**

To revert all mLDP MBB parameters to their default values: 
::

    dnRouter(cfg-protocols-ldp-mldp)# no make-before-break

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
