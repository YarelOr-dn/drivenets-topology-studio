services twamp admin-state
--------------------------

**Minimum user role:** operator

To enable or disable the TWAMP service:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services twamp

**Parameter table**

+-------------+-----------------------------------------+--------------+----------+
| Parameter   | Description                             | Range        | Default  |
+=============+=========================================+==============+==========+
| admin-state | The desired state of the TWAMP service. | | enabled    | disabled |
|             |                                         | | disabled   |          |
+-------------+-----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# admin-state enabled
    dnRouter(cfg-srv-twamp)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-twamp)# no admin-state

**Command History**

+---------+-------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                    |
+=========+=================================================================================================+
| 5.1.0   | Command introduced                                                                              |
+---------+-------------------------------------------------------------------------------------------------+
| 6.0     | Updated command services TWAMP mode changed to services TWAMP admin-state Applied new hierarchy |
+---------+-------------------------------------------------------------------------------------------------+
| 9.0     | TWAMP not supported                                                                             |
+---------+-------------------------------------------------------------------------------------------------+
| 11.2    | Command re-introduced                                                                           |
+---------+-------------------------------------------------------------------------------------------------+
