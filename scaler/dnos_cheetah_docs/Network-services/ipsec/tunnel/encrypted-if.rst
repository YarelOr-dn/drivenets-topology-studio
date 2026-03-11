network-services ipsec tunnel encrypted-if
------------------------------------------

**Minimum user role:** operator

Set the encrypted-if for the tunnel to connect to.

**Command syntax: encrypted-if [encrypted-if]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+--------------+-------------------------------------------+------------------+---------+
| Parameter    | Description                               | Range            | Default |
+==============+===========================================+==================+=========+
| encrypted-if | encrypted-if for the tunnel to connect to | | string         | \-      |
|              |                                           | | length 1-255   |         |
+--------------+-------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# encrypted-if ipsec-0


**Removing Configuration**

To remove the configuration of the encrypted-if:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no encrypted-if

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
