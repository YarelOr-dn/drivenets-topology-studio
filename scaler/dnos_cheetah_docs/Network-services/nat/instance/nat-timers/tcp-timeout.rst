network-services nat instance nat-timers tcp-timeout
----------------------------------------------------

**Minimum user role:** operator

Configure the NAT timeout value for the TCP sessions.

**Command syntax: tcp-timeout [tcp-timeout]**

**Command mode:** config

**Hierarchies**

- network-services nat instance nat-timers

**Parameter table**

+-------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter   | Description                                                                      | Range    | Default |
+=============+==================================================================================+==========+=========+
| tcp-timeout | Amount of time for idle TCP session to be retired from the NAPT session table.   | 10-10000 | 7440    |
|             | The default value is taken from RFC5382 Section 5                                |          |         |
+-------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)# nat-timers
    dnRouter(cfg-nat-inst-timers)# tcp-timeout 120
    dnRouter(cfg-nat-inst-timers)#


**Removing Configuration**

To set TCP timeout timer to default
::

    dnRouter(cfg-nat-inst-timers)# no tcp-timeout"

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
