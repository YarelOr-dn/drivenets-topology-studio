routing-policy qppb-policy
--------------------------

**Minimum user role:** operator

A QoS qppb policy is a set of rules and is identified by a unique name.

To create a QoS qppb policy:

**Command syntax: qppb-policy [qppb-policy]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Parameter table**

+-------------+------------------+------------------+---------+
| Parameter   | Description      | Range            | Default |
+=============+==================+==================+=========+
| qppb-policy | qppb policy name | | string         | \-      |
|             |                  | | length 1-255   |         |
+-------------+------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)#


**Removing Configuration**

To remove the qppb policy
::

    dnRouter(cfg-rpl)# no qppb-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
