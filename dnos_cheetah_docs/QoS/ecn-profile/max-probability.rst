qos ecn-profile max-probability
-------------------------------

**Minimum user role:** operator

To configure the ECN profile max-probability which is the maximum marking probability for the profile curve:

**Command syntax: max-probability [max-probability]**

**Command mode:** config

**Hierarchies**

- qos ecn-profile

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                      | Range | Default |
+=================+==================================================================================+=======+=========+
| max-probability | marking percentage at the max of the curve. The marking probability curve starts | 1-100 | 100     |
|                 | at 0 marking at min and reaches this marking probability at the max of the       |       |         |
|                 | curve. Beyond max, the marking probability jumps to 100%.                        |       |         |
+-----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1
    dnRouter(cfg-qos-MyEcnProfile1)# max-probability 50


**Removing Configuration**

To remove the max probability:
::

    dnRouter(cfg-qos-MyEcnProfile1)# no max-probability

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
