protocols lldp timers hold-time
-------------------------------

**Minimum user role:** operator

To adjust the LLDP hold-time timer:

**Command syntax: hold-time [hold-time]**

**Command mode:** config

**Hierarchies**

- protocols lldp timers

**Parameter table**

+-----------+----------------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                                      | Range    | Default |
+===========+==================================================================================+==========+=========+
| hold-time | Sets the amount of time (in seconds) that LLDP information is held before it is  | 30-65535 | 120     |
|           | discarded.                                                                       |          |         |
+-----------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# timers
    dnRouter(cfg-protocols-lldp-timers)# hold-time 90


**Removing Configuration**

To return the hold-time to its default value:
::

    dnRouter(cfg-protocols-lldp-timers)# no hold-time

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Command reintroduced          |
+---------+-------------------------------+
