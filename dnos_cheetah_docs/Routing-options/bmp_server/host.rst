routing-options bmp server host port
------------------------------------

**Minimum user role:** operator

To set the BMP server IP address and remote port for the BMP TCP session establishment.

**Command syntax: host [ip-address] port [dest-port]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Note**

- The host address and port must be configured for a BMP session to be established.

**Parameter table**

+------------+-------------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                             | Range        | Default |
+============+=========================================================================+==============+=========+
| ip-address | bmp server ip-address                                                   | | A.B.C.D    | \-      |
|            |                                                                         | | X:X::X:X   |         |
+------------+-------------------------------------------------------------------------+--------------+---------+
| dest-port  | destination tcp port to be used for the tcp session with the bmp server | 1-65535      | \-      |
+------------+-------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 2
    dnRouter(cfg-routing-option-bmp)# host 1.1.1.1 port 8000

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# host 1:1::1:1 port 8000


**Removing Configuration**

To remove the ip address and port configuration:
::

    dnRouter(cfg-routing-option-bmp)# no host

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
