network-services vrf instance protocols bgp router-id
-----------------------------------------------------

**Minimum user role:** operator

To set the router-ID of the BGP process:

**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- Changing the router-id will cause all BGP sessions to restart.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| router-id | Router id of the router - an unsigned 32-bit integer expressed in dotted quad    | A.B.C.D | \-      |
|           | notation. By default - the ipv4 address of lo0 interface                         |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# router-id 100.70.1.45


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-protocols-bgp)# no router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
