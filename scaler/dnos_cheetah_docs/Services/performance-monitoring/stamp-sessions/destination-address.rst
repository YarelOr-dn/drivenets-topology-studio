services performance-monitoring simple-twamp session destination-address
------------------------------------------------------------------------

**Minimum user role:** operator

To configure the destination IP address for the Simple TWAMP monitoring session:

**Command syntax: destination-address [ip-address]** vrf [vrf-name]

**Command mode:** config

**Hierarchies**

- services performance-monitoring simple-twamp session

**Parameter table**

+------------+----------------------+------------------+---------+
| Parameter  | Description          | Range            | Default |
+============+======================+==================+=========+
| ip-address | Reflector IP address | | A.B.C.D        | \-      |
|            |                      | | X:X::X:X       |         |
+------------+----------------------+------------------+---------+
| vrf-name   | Reflector VRF        | | string         | default |
|            |                      | | length 1-255   |         |
+------------+----------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)# destination-address 1.1.1.1

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)# destination-address 2.2.2.2 vrf MyVrf-1


**Removing Configuration**

To remove the configured destination IP address:
::

    dnRouter(cfg-srv-pm-stamp-session)# no destination-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
