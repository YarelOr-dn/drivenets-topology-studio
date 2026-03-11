services ipsec tunnel vrf device-public-ip
------------------------------------------

**Minimum user role:** operator

Set the device-public-ip of the device connecting to the ipsec gateway.

**Command syntax: device-public-ip [device-public-ip]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+------------------+---------------------------------------+------------+---------+
| Parameter        | Description                           | Range      | Default |
+==================+=======================================+============+=========+
| device-public-ip | IP address of the ipsec-gateway peer. | A.B.C.D    | \-      |
|                  |                                       | X:X::X:X   |         |
+------------------+---------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# device-public-ip 10.10.10.10


**Removing Configuration**

To remove the configuration of the device-public-ip:
::

    dnRouter(cfg-srv-ipsec-tun)# no device-public-ip

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
