services performance-monitoring interface delay-measurement dynamic-delay destination-address
---------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the destination IP address for the dynamic link delay monitoring session:

**Command syntax: destination-address [ip-address]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring interface delay-measurement dynamic-delay

**Parameter table**

+------------+--------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                        | Range        | Default |
+============+====================================================================+==============+=========+
| ip-address | The destination address for dynamic link delay monitoring session. | | A.B.C.D    | \-      |
|            |                                                                    | | X:X::X:X   |         |
+------------+--------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)# dynamic-delay
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# destination-address 1.1.1.1
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)#


**Removing Configuration**

To remove the configured destination IP address:
::

    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# no destination-address

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 18.0    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
