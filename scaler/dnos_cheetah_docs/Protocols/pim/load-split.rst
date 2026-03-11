protocols pim load-split admin-state
------------------------------------

**Minimum user role:** operator

To take advantage of multiple paths throughout the network, traffic from a multicast source or sources is load split across ECMP paths.

To enable/disable PIM's load-split:

**Command syntax: load-split admin-state [load-split-admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Parameter table**

+------------------------+--------------------------------+--------------+---------+
| Parameter              | Description                    | Range        | Default |
+========================+================================+==============+=========+
| load-split-admin-state | The PIM Load Split admin state | | enabled    | enabled |
|                        |                                | | disabled   |         |
+------------------------+--------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# load-split admin-state disabled
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no load-split admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
