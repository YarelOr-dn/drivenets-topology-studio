services performance-monitoring simple-twamp session admin-state
----------------------------------------------------------------

**Minimum user role:** operator

To enable or disable a Simple TWAMP monitoring session:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring simple-twamp session

**Parameter table**

+-------------+-----------------------------------------------------------+--------------+----------+
| Parameter   | Description                                               | Range        | Default  |
+=============+===========================================================+==============+==========+
| admin-state | The administrative state of the Simple TWAMP test-session | | enabled    | disabled |
|             |                                                           | | disabled   |          |
+-------------+-----------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-pm-stamp-session)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
