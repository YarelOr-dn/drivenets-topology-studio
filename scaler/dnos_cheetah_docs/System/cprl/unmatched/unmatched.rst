system cprl unmatched
---------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the Unmatched protocol:

**Command syntax: unmatched**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# unmatched
    dnRouter(cfg-system-cprl-unmatched)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the Unmatched protocol:
::

    dnRouter(cfg-system-cprl)# no unmatched

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
