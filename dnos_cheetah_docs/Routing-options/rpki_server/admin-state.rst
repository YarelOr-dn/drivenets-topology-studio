routing-options rpki server admin-state
---------------------------------------

**Minimum user role:** operator

To set the administrative state of the RPKI cache-server:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-------------+-------------------------------+--------------+---------+
| Parameter   | Description                   | Range        | Default |
+=============+===============================+==============+=========+
| admin-state | RPKI cache server admin-state | | enabled    | enabled |
|             |                               | | disabled   |         |
+-------------+-------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# admin-state disabled


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-routing-options-rpki)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
