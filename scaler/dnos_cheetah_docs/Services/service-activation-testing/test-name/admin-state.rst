services service-activation-testing test-name admin-state
---------------------------------------------------------

**Minimum user role:** operator

To enable or disable service-activation-testing testing:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services service-activation-testing test-name

**Parameter table**

+-------------+----------------------------------------------------------+--------------+----------+
| Parameter   | Description                                              | Range        | Default  |
+=============+==========================================================+==============+==========+
| admin-state | The default state of service-activation-testing service. | | enabled    | disabled |
|             |                                                          | | disabled   |          |
+-------------+----------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# service
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)# test-name test1
    dnRouter(cfg-srv-sat-test1)# admin-state enabled
    dnRouter(cfg-srv-sat-test1)#


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-sat-test1)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
