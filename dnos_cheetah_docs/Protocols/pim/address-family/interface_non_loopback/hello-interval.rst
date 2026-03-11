protocols pim address-family interface hello-interval
-----------------------------------------------------

**Minimum user role:** operator

To configure the hello interval on a specific PIM interface:

**Command syntax: hello-interval [hello-interval]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family interface

**Note**
- The derived hello hold-time is 3.5 x hello-interval and it must be greater than the graceful-restart-time.

**Parameter table**

+----------------+--------------------------------------+--------+---------+
| Parameter      | Description                          | Range  | Default |
+================+======================================+========+=========+
| hello-interval | Periodic interval for Hello messages | 1-3600 | \-      |
+----------------+--------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface ge100-1/2/1
    dnRouter(cfg-protocols-pim-af4-if)# hello-interval 24
    dnRouter(cfg-protocols-pim-af4-if)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface bundle-20.101
    dnRouter(cfg-protocols-pim-af4-if)# hello-interval 100
    dnRouter(cfg-protocols-pim-af4-if)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim-af4-if)# no hello-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
