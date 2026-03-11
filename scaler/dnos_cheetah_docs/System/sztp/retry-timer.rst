system sztp retry-timer
-----------------------

**Minimum user role:** admin

The retry timer specifies the waiting period before reattempting the SZTP flow after a failed attempt to complete it in all the configured Bootstrap servers.

**Command syntax: retry-timer [retry-timer]**

**Command mode:** config

**Hierarchies**

- system sztp

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                                      | Range  | Default |
+=============+==================================================================================+========+=========+
| retry-timer | controls the interval in seconds between attempts to contact the bootstrap       | 5-3600 | 60      |
|             | server                                                                           |        |         |
+-------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# retry-timer 20


**Removing Configuration**

To revert retry-timer to default:
::

    dnRouter(cfg-system-sztp)# no retry-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
