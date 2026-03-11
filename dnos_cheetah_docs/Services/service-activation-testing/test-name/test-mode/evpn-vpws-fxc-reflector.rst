services service-activation-testing test-name test-mode evpn-vpws-fxc-reflector evpn-vpws-fxc normalized-stag
-------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the service and customer paremeters for reflection per specific test-name.\n\n
Customers are identified by the combination :  {normalized S Vlan ID , C vlan id ,evpn-vpws-fxc instance} \n\n
Supported tests are as defined by RFC2544 and Y.1564 as reflector.\n\n
It is operator responsability to verify \n\n
1. ONLY test traffic is in presence during test \n\n
2. Test traffic rate should be lower of equell the slowest path (up-link \ down link) \n\n
To configure the test mode:

**Command syntax: evpn-vpws-fxc-reflector evpn-vpws-fxc [evpn-vpws-fxc] normalized-stag [normalized-stag]** normalized-ctag [normalized-ctag]

**Command mode:** config

**Hierarchies**

- services service-activation-testing test-name test-mode

**Parameter table**

+-----------------+------------------------------------------------------------+------------------+---------+
| Parameter       | Description                                                | Range            | Default |
+=================+============================================================+==================+=========+
| evpn-vpws-fxc   | Service instance name for the Service Reflector test mode. | | string         | \-      |
|                 |                                                            | | length 1-255   |         |
+-----------------+------------------------------------------------------------+------------------+---------+
| normalized-stag | Identification number for the Service Tag.                 | 1-4094           | \-      |
+-----------------+------------------------------------------------------------+------------------+---------+
| normalized-ctag | Identification number for the customer tag.                | 1-4094           | \-      |
+-----------------+------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)# test-name test1
    dnRouter(cfg-srv-sat-test1)# test-mode
    dnRouter(cfg-srv-sat-test1-test-mode)# evpn-vpws-fxc-reflector evpn-vpws-fxc 10 normalized-stag 2 normalized-ctag 100
    dnRouter(cfg-srv-sat-test1-test-mode)#


**Removing Configuration**

To remove the test mode configuration:
::

    dnRouter(cfg-srv-sat-test1)# no test-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
