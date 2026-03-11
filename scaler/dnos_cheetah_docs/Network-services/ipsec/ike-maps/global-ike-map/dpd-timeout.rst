network-services ipsec ike-maps global-ike-map dpd-timeout
----------------------------------------------------------

**Minimum user role:** operator

Set the dead peer detection timeout for the tunnel. After this timeout, if no packets are received from the peer, also for dpd probes, the tunnel will close.

**Command syntax: dpd-timeout [dpd-timeout]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map

**Parameter table**

+-------------+-----------------------------+--------+---------+
| Parameter   | Description                 | Range  | Default |
+=============+=============================+========+=========+
| dpd-timeout | dead peer detection timeout | 30-600 | 30      |
+-------------+-----------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# dpd-timeout 30


**Removing Configuration**

To remove the configuration of the dpd-timeout:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no dpd-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
