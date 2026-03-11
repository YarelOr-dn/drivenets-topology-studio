services service-activation-testing test-name test-mode
-------------------------------------------------------

**Minimum user role:** operator

Configure the type of test mode to be conducted for service-activation-testing.

To configure the test mode:

**Command syntax: test-mode**

**Command mode:** config

**Hierarchies**

- services service-activation-testing test-name

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)# test-name test1
    dnRouter(cfg-srv-sat-test1)# test-mode
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
