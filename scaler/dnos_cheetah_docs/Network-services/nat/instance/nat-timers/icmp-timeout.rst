network-services nat instance nat-timers icmp-timeout
-----------------------------------------------------

**Minimum user role:** operator

Configure the NAT timeout value for ICMP sessions.

**Command syntax: icmp-timeout [icmp-timeout]**

**Command mode:** config

**Hierarchies**

- network-services nat instance nat-timers

**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter    | Description                                                                      | Range    | Default |
+==============+==================================================================================+==========+=========+
| icmp-timeout | Amount of time for idle ICMP session to be retired from the NAPT session table.  | 10-10000 | 60      |
|              | The default value is taken from RFC5508 Section 3.2                              |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# nat-timers
    dnRouter(cfg-nat-inst-timers)# icmp-timeout 120
    dnRouter(cfg-nat-inst-timers)#


**Removing Configuration**

To set ICMP timeout timer to default
::

    dnRouter(cfg-nat-inst-timers)# no icmp-timeout"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
