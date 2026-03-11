network-services multihoming interface no-startup-delay
-------------------------------------------------------

**Minimum user role:** operator

Prevents the startup-delay to be applied on this multihomed parent interface (physical interfaces or bundles).
The delay (if configured under multihoming) would normally have been applied upon startup after a power-cycle,
cold-restart or warm-restart on all the multihomed interfaces.

**Command syntax: no-startup-delay**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# no-startup-delay


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh)# no no-startup-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
