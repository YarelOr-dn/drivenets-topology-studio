system ntp
----------

**Minimum user role:** operator

Enter the NTP configuration hierarchy.

**Command syntax: ntp**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)#


**Removing Configuration**

To remove NTP configuration:
::

    no ntp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
