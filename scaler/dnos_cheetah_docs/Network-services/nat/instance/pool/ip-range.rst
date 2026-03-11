network-services nat instance pool start-address end-address
------------------------------------------------------------

**Minimum user role:** operator

Configure consecutive IP ranges (the first IP address in the range and the last IP address in the range) for the IP pool.

**Command syntax: start-address [start-address] end-address [end-address]**

**Command mode:** config

**Hierarchies**

- network-services nat instance pool

**Note**

- IPv4 addresses only.

**Parameter table**

+---------------+------------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                      | Range   | Default |
+===============+==================================================================+=========+=========+
| start-address | Reference to the configured start-address within an address pool | A.B.C.D | \-      |
+---------------+------------------------------------------------------------------+---------+---------+
| end-address   | Reference to the configured end-address within an address pool   | A.B.C.D | \-      |
+---------------+------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# pool myPool
    dnRouter(cfg-nat-inst-pool)# start-address START-ADDRESS end-address END-ADDRESS
    dnRouter(cfg-nat-inst-pool)#


**Removing Configuration**

To remove the specified range from the pool
::

    dnRouter(cfg-nat-inst-pool)# no start-address START-ADDRESS end-address END-ADDRESS

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
