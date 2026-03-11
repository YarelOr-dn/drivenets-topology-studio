protocols ldp multipoint make-before-break admin-state
------------------------------------------------------

**Minimum user role:** operator

To enable or disable the multipoint LDP make-before-break capability:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp multipoint make-before-break

**Parameter table**

+-------------+-----------------------------------------------+--------------+----------+
| Parameter   | Description                                   | Range        | Default  |
+=============+===============================================+==============+==========+
| admin-state | Administratively sets the mLDP MBB capability | | enabled    | disabled |
|             |                                               | | disabled   |          |
+-------------+-----------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)# mbb
    dnRouter(cfg-ldp-mldp-mbb)# admin-state enabled


**Removing Configuration**

To revert the mLDP MBB administrative state to its default value: 
::

    dnRouter(cfg-ldp-mldp-mbb)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
