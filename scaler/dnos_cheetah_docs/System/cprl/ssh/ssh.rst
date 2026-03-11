system cprl ssh
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the SSH protocol:

**Command syntax: ssh**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ssh
    dnRouter(cfg-system-cprl-ssh)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the SSH protocol:
::

    dnRouter(cfg-system-cprl)# no ssh

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
