protocols lldp timers keep-alive
--------------------------------

**Minimum user role:** operator

To adjust the LLDP keep-alive timer:

**Command syntax: keep-alive [keep-alive]**

**Command mode:** config

**Hierarchies**

- protocols lldp timers

**Parameter table**

+------------+---------------------------------------------------+----------+---------+
| Parameter  | Description                                       | Range    | Default |
+============+===================================================+==========+=========+
| keep-alive | frequency at which LLDP advertisements are sent . | 30-65535 | 30      |
+------------+---------------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# timers
    dnRouter(cfg-protocols-lldp-timers)# keep-alive 30


**Removing Configuration**

To return the keep-alive to its default value:
::

    dnRouter(cfg-protocols-lldp-timers)# no keep-alive

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
