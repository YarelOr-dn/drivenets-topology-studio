protocols segment-routing mpls policy-reoptimization
----------------------------------------------------

**Minimum user role:** operator

Paths may become invalid in time due to topology changes. When a policy has multiple path options and a better priority path becomes invalid, the system will use the next preferred priority path. The policy will continue using the worse priority path even if the better priority path is available again. To fix this, you can globally set a policy reoptimization interval that will cause the system to instruct all segment-routing policies that are not on the best path to attempt to use a better priority path.

To configure the policy reoptimization interval:

**Command syntax: policy-reoptimization [policy-reoptimization]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Note**
-  Interval 0 will disable periodic optimization.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter             | Description                                                                      | Range   | Default |
+=======================+==================================================================================+=========+=========+
| policy-reoptimization | Configure the period of time after which global policy optimization will be      | 0-65535 | 60      |
|                       | attempted                                                                        |         |         |
+-----------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy-reoptimization 5


**Removing Configuration**

To return the interval to its default value:
::

    dnRouter(cfg-protocols-sr-mpls)# no policy-reoptimization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
