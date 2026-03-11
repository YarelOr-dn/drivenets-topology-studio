routing-options rpki server
---------------------------

**Minimum user role:** operator

To configure a BGP RPKI cache server and its remote address.

**Command syntax: rpki server [server-address]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Multiple RPKI cache-servers can be configured for redundancy.

- Sessions are established simultaneously with all the configured RPKI cache-servers.

**Parameter table**

+----------------+------------------------------------------+-------+---------+
| Parameter      | Description                              | Range | Default |
+================+==========================================+=======+=========+
| server-address | RPKI cache server IP address or hotsname | \-    | \-      |
+----------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)#

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 2001:125:125::1
    dnRouter(cfg-routing-options-rpki)#

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)#


**Removing Configuration**

To revert all RPKI cache-server's configuration to the default values:
::

    dnRouter(cfg-routing-options)# no rpki server 1.1.1.1

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 15.1    | Command introduced                                   |
+---------+------------------------------------------------------+
| 16.2    | Replaced server identifier with the server's address |
+---------+------------------------------------------------------+
