services service-activation-testing test-name test-mode interface-reflector
---------------------------------------------------------------------------

**Minimum user role:** operator

Configure the type of test and interface to be reflected by service-activation-testing.
The device will reflect all packets that will arriv to this interface as required by standard RFC2544 and Y.1564 
It is assumed that only test traffic will arrive to/from this interface during test procedure.

To configure the test mode:

**Command syntax: interface-reflector [interface]**

**Command mode:** config

**Hierarchies**

- services service-activation-testing test-name test-mode

**Parameter table**

+-----------+----------------------------------------------------+------------------+---------+
| Parameter | Description                                        | Range            | Default |
+===========+====================================================+==================+=========+
| interface | Select interface reflector test-mode for the test. | | string         | \-      |
|           |                                                    | | length 1-255   |         |
+-----------+----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)# test-name test1
    dnRouter(cfg-srv-sat-test1)# test-mode interface-reflector ge400-6/0/1
    dnRouter(cfg-srv-sat-test1)#


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
