routing-options bmp server route-monitoring adj-in post-policy
--------------------------------------------------------------

**Minimum user role:** operator

Enable exporting BGP neighbor adjacency-in post-policy tables. The configuration applies to all BGP neighbor address-families.

**Command syntax: adj-in post-policy [admin-state]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server route-monitoring

**Parameter table**

+-------------+--------------------------------+--------------+----------+
| Parameter   | Description                    | Range        | Default  |
+=============+================================+==============+==========+
| admin-state | adjecenty in post policy table | | enabled    | disabled |
|             |                                | | disabled   |          |
+-------------+--------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# route-monitoring
    dnRouter(cfg-routing-option-bmp-rm)# adj-in post-policy enabled


**Removing Configuration**

To return the admin-state to the default value:
::

    dnRouter(cfg-routing-option-bmp)# no adj-in post-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
