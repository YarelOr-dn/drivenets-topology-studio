services ipsec tunnel vrf auth-method
-------------------------------------

**Minimum user role:** operator

Set the authentication method for the device connecting to the ipsec gateway.

**Command syntax: auth-method [auth-method]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+-------------+----------------------------------------------------------------------+---------------------+------------+
| Parameter   | Description                                                          | Range               | Default    |
+=============+======================================================================+=====================+============+
| auth-method | Type of authentication method (pre-shared, digital signature, null). | pre-shared          | pre-shared |
|             |                                                                      | digital-signature   |            |
|             |                                                                      | null                |            |
+-------------+----------------------------------------------------------------------+---------------------+------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# auth-method psk


**Removing Configuration**

To remove the configuration of the auth method and return to default:
::

    dnRouter(cfg-srv-ipsec-tun)# no auth-method

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
