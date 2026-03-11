protocols segment-routing pcep admin-state
------------------------------------------

**Minimum user role:** operator

To enable or disable the PCEP protocol:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Parameter table**

+-------------+----------------------+--------------+----------+
| Parameter   | Description          | Range        | Default  |
+=============+======================+==============+==========+
| admin-state | enable pcep protocol | | enabled    | disabled |
|             |                      | | disabled   |          |
+-------------+----------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# admin-state enabled


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-protocols-sr-pcep)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
