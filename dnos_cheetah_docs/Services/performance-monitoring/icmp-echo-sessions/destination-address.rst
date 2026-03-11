services performance-monitoring icmp-echo session destination-address
---------------------------------------------------------------------

**Minimum user role:** operator

To configure the destination IP address for the ICMP echo IP performance monitoring session:

**Command syntax: destination-address [ip-address]** vrf [vrf-name]

**Command mode:** config

**Hierarchies**

- services performance-monitoring icmp-echo session

**Parameter table**

+------------+-------------------+------------------+---------+
| Parameter  | Description       | Range            | Default |
+============+===================+==================+=========+
| ip-address | Target IP address | | A.B.C.D        | \-      |
|            |                   | | X:X::X:X       |         |
+------------+-------------------+------------------+---------+
| vrf-name   | Target VRF        | | string         | default |
|            |                   | | length 1-255   |         |
+------------+-------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)# destination-address 1.1.1.1

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)# destination-address 2.2.2.2 vrf MyVrf-1


**Removing Configuration**

To remove the configured destination IP address:
::

    dnRouter(cfg-srv-pm-icmp-echo-session)# no destination-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
