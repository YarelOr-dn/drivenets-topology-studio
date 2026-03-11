network-services nat instance bypass-list
-----------------------------------------

**Minimum user role:** operator

To configure the list of 3-tuple flows that must not undergo NAT translation while forwarded from internal-if toward external-if and vice versa.

**Command syntax: bypass-list [list]**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Note**

- Only “allow” rules in the ACL will be referred with 3-tuple pattern.

- src-ip/dest-ip must be /32 addresses.

- The protocol must be either tcp(0x06) or udp(0x17).

- Other rules will not be referred.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| list      | List of 5-tuple sessions that should not be subjected to NAT/NAPT translations.  | \-    | \-      |
|           | Represented by the ACL list. Only 'allow' rules in the ACL will be referred with |       |         |
|           | full 5-tuple pattern                                                             |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# bypass-list bypassACL
    dnRouter(cfg-netsrv-nat-inst)#


**Removing Configuration**

To remove the bypass-list from specified NAT instance
::

    dnRouter(cfg-netsrv-nat)# no bypass-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
