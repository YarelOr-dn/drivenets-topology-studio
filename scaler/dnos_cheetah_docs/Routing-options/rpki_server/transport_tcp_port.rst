routing-options rpki server transport tcp port
----------------------------------------------

**Minimum user role:** operator

To configure the port for the TCP transport session with the BGP RPKI cache-server.

**Command syntax: transport tcp port [tcp-port]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-----------+------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                            | Range   | Default |
+===========+========================================================================+=========+=========+
| tcp-port  | Destination port to be used for the session with the RPKI cache server | 1-65535 | \-      |
+-----------+------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport tcp port 323


**Removing Configuration**

To remove the configured TCP port:
::

    dnRouter(cfg-routing-options-rpki)# no transport tcp port

To remove the configured transport configuration:
::

    dnRouter(cfg-routing-options-rpki)# no transport

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
