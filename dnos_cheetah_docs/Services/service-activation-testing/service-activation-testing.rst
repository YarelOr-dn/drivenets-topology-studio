services service-activation-testing
-----------------------------------

**Minimum user role:** operator

To enter the service-activation-testing configuration hierarchy:

**Command syntax: service-activation-testing**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)#


**Removing Configuration**

To revert all service-activation-testing configuration to default:
::

    dnRouter(cfg-srv)# no service-activation-testing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
