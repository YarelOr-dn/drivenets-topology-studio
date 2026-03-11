network-services ipsec tunnel description
-----------------------------------------

**Minimum user role:** operator

Set the description of the tunnel provided by the user.

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+-------------+------------------------------------------+------------------+---------+
| Parameter   | Description                              | Range            | Default |
+=============+==========================================+==================+=========+
| description | The name of the tunnel provided by user. | | string         | \-      |
|             |                                          | | length 1-255   |         |
+-------------+------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# description MyTunnel


**Removing Configuration**

To remove the configuration of the tunnel description:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
