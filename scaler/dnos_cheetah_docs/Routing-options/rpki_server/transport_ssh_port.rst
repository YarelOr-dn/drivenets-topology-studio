routing-options rpki server transport ssh port
----------------------------------------------

**Minimum user role:** operator

To configure the port for the SSH transport session with the BGP RPKI cache-server.

**Command syntax: transport ssh port [ssh-port]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+-----------+------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                            | Range   | Default |
+===========+========================================================================+=========+=========+
| ssh-port  | Destination port to be used for the session with the RPKI cache server | 1-65535 | \-      |
+-----------+------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport ssh port 323


**Removing Configuration**

To remove the configured SSH port:
::

    dnRouter(cfg-routing-options-rpki)# no transport ssh port

To remove the configured transport configuration:
::

    dnRouter(cfg-routing-options-rpki)# no transport

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
