routing-options rpki server retry-interval
------------------------------------------

**Minimum user role:** operator

To set the retry-interval value for the RTR session with the BGP RPKI cache server.

**Command syntax: retry-interval [retry-interval]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                                      | Range  | Default |
+================+==================================================================================+========+=========+
| retry-interval | Configures the time BGP waits for a response after sending a serial or reset     | 1-7200 | 600     |
|                | query. Set retry-interval in seconds.                                            |        |         |
+----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# retry-interval 600


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no retry-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
