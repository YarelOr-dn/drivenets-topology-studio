system cprl vrrp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the VRRP protocol:

**Command syntax: vrrp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# vrrp
    dnRouter(cfg-system-cprl-vrrp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the VRRP protocol:
::

    dnRouter(cfg-system-cprl)# no vrrp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
