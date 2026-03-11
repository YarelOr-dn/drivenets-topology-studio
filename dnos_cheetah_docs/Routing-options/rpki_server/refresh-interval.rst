routing-options rpki server refresh-interval
--------------------------------------------

**Minimum user role:** operator

To set the refresh-interval value for the RTR session with the BGP RPKI cache server.

**Command syntax: refresh-interval [refresh-interval]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                                      | Range   | Default |
+==================+==================================================================================+=========+=========+
| refresh-interval | Configures the time BGP waits in before next periodic attempt to poll the cache  | 1-86400 | 3600    |
|                  | and between subsequent attempts. Set refresh-interval in seconds.                |         |         |
+------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# refresh-interval 3600


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no refresh-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
