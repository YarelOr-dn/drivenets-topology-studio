network-services ipsec tunnel
-----------------------------

**Minimum user role:** operator

Configuration of the device which will connect to IPSec gateway.

**Command syntax: tunnel [tunnel]**

**Command mode:** config

**Hierarchies**

- network-services ipsec

**Parameter table**

+-----------+-------------------------------+-------+---------+
| Parameter | Description                   | Range | Default |
+===========+===============================+=======+=========+
| tunnel    | unique identifier per device. | \-    | \-      |
+-----------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)#


**Removing Configuration**

To remove the tunnel configurations:
::

    dnRouter(cfg-netsrv-ipsec)# no tunnel 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
