services ipsec terminator max-tunnels-scale
-------------------------------------------

**Minimum user role:** operator

Maximal numer of tunnels the IPSec terminator can hold

**Command syntax: max-tunnels-scale [max-tunnels-scale]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+-------------------+--------------------------------------------------+--------------+---------+
| Parameter         | Description                                      | Range        | Default |
+===================+==================================================+==============+=========+
| max-tunnels-scale | max tunnels number the ipsec terminator can hold | 0-4294967295 | \-      |
+-------------------+--------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1 max-tunnels-scale 200


**Removing Configuration**

To revert the max tunnel scale to the default value:
::

    dnRouter(cfg-srv-ipsec)# no max-tunnel-scale

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
