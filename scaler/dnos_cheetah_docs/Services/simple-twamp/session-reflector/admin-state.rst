services simple-twamp session-reflector admin-state
---------------------------------------------------

**Minimum user role:** operator

To enable or disable the Simple TWAMP Session-Reflector:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services simple-twamp session-reflector

**Parameter table**

+-------------+----------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                    | Range        | Default  |
+=============+================================================================+==============+==========+
| admin-state | The administrative state of the Simple TWAMP Session-Reflector | | enabled    | disabled |
|             |                                                                | | disabled   |          |
+-------------+----------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-reflector
    dnRouter(cfg-srv-stamp-reflector)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-stamp-reflector)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
