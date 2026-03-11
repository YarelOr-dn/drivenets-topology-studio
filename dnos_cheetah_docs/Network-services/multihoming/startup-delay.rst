network-services multihoming startup-delay
------------------------------------------

**Minimum user role:** operator

Sets the startup-delay to be applied on all multihomed parent interfaces (physical interfaces or bundles).
The delay is applied upon startup after power-cycle, cold-restart or warm-restart.

**Command syntax: startup-delay [startup-delay]**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Parameter table**

+---------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                                      | Range   | Default |
+===============+==================================================================================+=========+=========+
| startup-delay | Delay in seconds to apply to multihomed interfaces upon startup of the           | 60-1800 | \-      |
|               | interface, while keeping the laser-off                                           |         |         |
+---------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# startup-delay 500
    dnRouter(cfg-netsrv-mh)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh)# no startup-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
