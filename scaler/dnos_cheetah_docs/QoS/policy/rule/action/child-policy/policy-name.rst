qos policy rule action child-policy policy-name
-----------------------------------------------

**Minimum user role:** operator

Attach a child policy to a hierarchical policy.

 The child policy action can be applied on rule default of a hierarchical policy, to specify a classification or queuing policy. 

**Command syntax: policy-name [policy-name]**

**Command mode:** config

**Hierarchies**

- qos policy rule action child-policy

**Parameter table**

+-------------+-------------+------------------+---------+
| Parameter   | Description | Range            | Default |
+=============+=============+==================+=========+
| policy-name | policy name | | string         | \-      |
|             |             | | length 1-255   |         |
+-------------+-------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule default
    dnRouter(cfg-policy-MyQoSPOlicy1-rule-default)# action
    dnRouter(cfg-myPolicy1-rule-default-action)# child-policy
    dnRouter(cfg-rule-default-action-child-policy)# policy-name MyPolicyA


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-rule-default-action-child-policy)# no policy-name

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
