protocols lldp admin-state
--------------------------

**Minimum user role:** operator

To enable LLDP admin-state (LLDP admin-state is disabled by default):

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Parameter table**

+-------------+-----------------------------------------+--------------+---------+
| Parameter   | Description                             | Range        | Default |
+=============+=========================================+==============+=========+
| admin-state | System level state of the LLDP protocol | | enabled    | enabled |
|             |                                         | | disabled   |         |
+-------------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# admin-state enabled


**Removing Configuration**

To return LLDP admin-state to its default value:
::

    dnRouter(cfg-protocols-lldp)# no admin-state

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 7.0     | Command introduced                                         |
+---------+------------------------------------------------------------+
| 9.0     | Not supported in this version                              |
+---------+------------------------------------------------------------+
| 10.0    | Command reintroduced with admin-state "enabled" by default |
+---------+------------------------------------------------------------+
| 16.1    | Updated command with admin-state "disabled" by default     |
+---------+------------------------------------------------------------+
