qos policy description
----------------------

**Minimum user role:** operator

To add a meaningful description for a policy:

**Command syntax: description [descr]**

**Command mode:** config

**Hierarchies**

- qos policy

**Parameter table**

+-----------+--------------------+------------------+---------+
| Parameter | Description        | Range            | Default |
+===========+====================+==================+=========+
| descr     | Policy description | | string         | \-      |
|           |                    | | length 1-255   |         |
+-----------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-policy-MyQoSPOlicy1)# description "Ingress peer 1 policy"


**Removing Configuration**

To remove the description from the policy
::

    dnRouter(cfg-policy-MyQoSPOlicy1)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
