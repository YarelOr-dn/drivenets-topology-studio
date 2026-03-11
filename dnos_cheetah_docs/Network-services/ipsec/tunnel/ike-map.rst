network-services ipsec tunnel ike-map
-------------------------------------

**Minimum user role:** operator

Set the ike map the tunnel should use.

**Command syntax: ike-map [ike-map]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+-----------+-------------------------------------------------+------------------+---------+
| Parameter | Description                                     | Range            | Default |
+===========+=================================================+==================+=========+
| ike-map   | reference to configured ike map for this tunnel | | string         | \-      |
|           |                                                 | | length 1-255   |         |
+-----------+-------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# ike-map MyIkeMap


**Removing Configuration**

To remove the configuration of the tunnel ike-map:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no ike-map

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
