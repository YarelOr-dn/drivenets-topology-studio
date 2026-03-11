network-services ipsec tunnel device-public-ip
----------------------------------------------

**Minimum user role:** operator

Set the device-public-ip of the device connecting to the ipsec gateway.

**Command syntax: device-public-ip [device-public-ip]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+------------------+---------------------------------------+--------------+---------+
| Parameter        | Description                           | Range        | Default |
+==================+=======================================+==============+=========+
| device-public-ip | IP address of the ipsec-gateway peer. | | A.B.C.D    | \-      |
|                  |                                       | | X:X::X:X   |         |
+------------------+---------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# device-public-ip 10.10.10.10


**Removing Configuration**

To remove the configuration of the device-public-ip:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no device-public-ip

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
