system cprl telnet
------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the Telnet protocol:

**Command syntax: telnet**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# telnet
    dnRouter(cfg-system-cprl-telnet)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the Telnet protocol:
::

    dnRouter(cfg-system-cprl)# no telnet

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
