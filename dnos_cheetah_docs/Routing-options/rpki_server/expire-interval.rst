routing-options rpki server expire-interval
-------------------------------------------

**Minimum user role:** operator

To set the expire-interval value for the RTR session with the BGP RPKI cache server:

**Command syntax: expire-interval [expire-interval]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter       | Description                                                                      | Range      | Default |
+=================+==================================================================================+============+=========+
| expire-interval | Configures the time BGP waits to keep routes from a cache after the cache        | 360-172800 | 7200    |
|                 | session drops. Set expire-interval in seconds.                                   |            |         |
+-----------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# expire-interval 7200


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no expire-interval

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 15.1    | Command introduced                       |
+---------+------------------------------------------+
| 16.1    | Modified the expire-interval lower bound |
+---------+------------------------------------------+
