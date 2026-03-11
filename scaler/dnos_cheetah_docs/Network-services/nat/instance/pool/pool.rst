network-services nat instance pool
----------------------------------

**Minimum user role:** operator

Configure a list of IP ranges for the external IP addresses pool in the N:M NAT translation.

**Command syntax: pool [pool-name]**

**Command mode:** config

**Hierarchies**

- network-services nat instance

**Note**

- The legal string length is 1..255 characters.

- Illegal characters include any whitespace, non-ascii, and the following special characters (separated by commas): #,!,',”,\

**Parameter table**

+-----------+---------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                               | Range            | Default |
+===========+===========================================================================+==================+=========+
| pool-name | a list of IP ranges for external IP addresses pool in N:M NAT translation | | string         | \-      |
|           |                                                                           | | length 1-255   |         |
+-----------+---------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# pool myPool
    dnRouter(cfg-nat-inst-pool)#


**Removing Configuration**

To remove the specified address pool
::

    dnRouter(cfg-netsrv-nat-inst)# no pool myPool

To remove all the address pool
::

    dnRouter(cfg-netsrv-nat-inst)# no pool

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
