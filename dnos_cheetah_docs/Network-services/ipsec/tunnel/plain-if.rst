network-services ipsec tunnel plain-if
--------------------------------------

**Minimum user role:** operator

Set the plain-if for the tunnel to connect to.

**Command syntax: plain-if [plain-if]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+-----------+---------------------------------------+------------------+---------+
| Parameter | Description                           | Range            | Default |
+===========+=======================================+==================+=========+
| plain-if  | plain-if for the tunnel to connect to | | string         | \-      |
|           |                                       | | length 1-255   |         |
+-----------+---------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# plain-if ipsec-1


**Removing Configuration**

To remove the configuration of the plain-if:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no plain-if

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
