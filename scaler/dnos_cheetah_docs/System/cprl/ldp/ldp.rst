system cprl ldp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the LDP protocol:

**Command syntax: ldp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ldp
    dnRouter(cfg-system-cprl-ldp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the LDP protocol:
::

    dnRouter(cfg-system-cprl)# no ldp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
