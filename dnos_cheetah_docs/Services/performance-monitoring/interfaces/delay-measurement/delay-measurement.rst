services performance-monitoring interface delay-measurement
-----------------------------------------------------------

**Minimum user role:** operator

Dynamic link delay is calculated by Simple-TWAMP (STAMP) link delay sessions. On a given interface/sub-interface, either an IPv4 Simple-TWAMP session or an IPv6 Simple-TWAMP session can be enabled. 
The sessions' link delay results will feed the ISIS Single-Topology or the ISIS Multi-Topology, for both IPv4 and IPv6 topologies. 
Link delay parameters are advertised under TLV 22 for IPv4 topology, TLV 222 for IPv6 topology, and ASLA sub-TLV, if enabled in ISIS and Flex-Algo is configured. 
The supported parameters are Min/Max unidirectional link delay, average link delay, and unidirectional delay variation.

**Command syntax: delay-measurement**

**Command mode:** config

**Hierarchies**

- services performance-monitoring interface

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)#


**Removing Configuration**

To remove the performance monitoring configurations:
::

    dnRouter(cfg-srv-pm-ge100-0/0/0)# no delay-measurement

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.1    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
