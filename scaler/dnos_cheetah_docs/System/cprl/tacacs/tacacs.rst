system cprl tacacs
------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the TACACS protocol:

**Command syntax: tacacs**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# tacacs
    dnRouter(cfg-system-cprl-tacacs)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the TACACS protocol:
::

    dnRouter(cfg-system-cprl)# no tacacs

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
