services service-activation-testing test-name
---------------------------------------------

**Minimum user role:** operator

Set a name for service-activation-testing
To configure service-activation-testing:

**Command syntax: test-name [tests]**

**Command mode:** config

**Hierarchies**

- services service-activation-testing

**Parameter table**

+-----------+---------------+-------+---------+
| Parameter | Description   | Range | Default |
+===========+===============+=======+=========+
| tests     | Set test name | \-    | \-      |
+-----------+---------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# service-activation-testing
    dnRouter(cfg-srv-sat)# test-name test1
    dnRouter(cfg-srv-sat-test1)#


**Removing Configuration**

To remove a specific test:
::

    dnRouter(cfg-srv-sat)#no test test1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
