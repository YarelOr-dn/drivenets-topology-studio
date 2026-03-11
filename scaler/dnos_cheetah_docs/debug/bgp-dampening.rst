debug bgp dampening
-------------------

**Minimum user role:** operator

To debug BGP dampening:

**Command syntax: bgp dampening**

**Command mode:** config

**Hierarchies**

- debug

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# debug
    dnRouter(cfg-debug)# bgp dampening


**Removing Configuration**

To remove debug configuration:
::

    dnRouter(cfg-debug)# no bgp dampening

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
