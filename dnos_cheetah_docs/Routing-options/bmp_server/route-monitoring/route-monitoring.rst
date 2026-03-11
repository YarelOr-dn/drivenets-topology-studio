routing-options bmp server route-monitoring
-------------------------------------------

**Minimum user role:** operator

To enter the BMP server route-monitoring configuration level. This allows you to define which BGP tables are exported by default to the BMP server.

**Command syntax: route-monitoring**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# route-monitoring
    dnRouter(cfg-routing-option-bmp-rm)#


**Removing Configuration**

To return the route-monitoring to the default value:
::

    dnRouter(cfg-routing-option-bmp)# no route-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
