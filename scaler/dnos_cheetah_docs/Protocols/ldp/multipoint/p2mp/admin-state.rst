protocols ldp multipoint p2mp admin-state
-----------------------------------------

**Minimum user role:** operator

To enable or disable the multipoint LDP point-to-multipoint capability:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp multipoint p2mp

**Parameter table**

+-------------+------------------------------------------------+--------------+----------+
| Parameter   | Description                                    | Range        | Default  |
+=============+================================================+==============+==========+
| admin-state | Administratively sets the mLDP P2MP capability | | enabled    | disabled |
|             |                                                | | disabled   |          |
+-------------+------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# multipoint
    dnRouter(cfg-protocols-ldp-mldp)# p2mp
    dnRouter(cfg-ldp-mldp-p2mp)# admin-state enabled


**Removing Configuration**

To revert the mLDP P2MP administrative state to its default value: 
::

    dnRouter(cfg-ldp-mldp-p2mp)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
