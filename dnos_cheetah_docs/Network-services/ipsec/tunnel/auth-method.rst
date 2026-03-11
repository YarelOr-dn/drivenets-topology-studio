network-services ipsec tunnel auth-method
-----------------------------------------

**Minimum user role:** operator

Set the authentication method for the device connecting to the ipsec gateway.

**Command syntax: auth-method [auth-method]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+-------------+----------------------------------------------------------------------+-----------------------+------------+
| Parameter   | Description                                                          | Range                 | Default    |
+=============+======================================================================+=======================+============+
| auth-method | Type of authentication method (pre-shared, digital signature, null). | | pre-shared          | pre-shared |
|             |                                                                      | | digital-signature   |            |
|             |                                                                      | | null                |            |
+-------------+----------------------------------------------------------------------+-----------------------+------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# auth-method psk


**Removing Configuration**

To remove the configuration of the auth method and return to default:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no auth-method

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
