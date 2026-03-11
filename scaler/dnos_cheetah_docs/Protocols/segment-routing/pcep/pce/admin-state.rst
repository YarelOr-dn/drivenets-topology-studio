protocols segment-routing pcep pce priority address admin-state
---------------------------------------------------------------

**Minimum user role:** operator

To enable or disable the PCEP protocol:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep pce priority address

**Parameter table**

+-------------+---------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                   | Range        | Default |
+=============+===============================================================+==============+=========+
| admin-state | set whether the pce server is available or not for delegation | | enabled    | \-      |
|             |                                                               | | disabled   |         |
+-------------+---------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# admin-state enabled


**Removing Configuration**

To revert admin-state to its default value:
::

    dnRouter(cfg-sr-pcep-pce)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
