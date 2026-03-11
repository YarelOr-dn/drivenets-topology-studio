system cprl dns
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the DNS protocol:

**Command syntax: dns**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# dns
    dnRouter(cfg-system-cprl-dns)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the DNS protocol:
::

    dnRouter(cfg-system-cprl)# no dns

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
