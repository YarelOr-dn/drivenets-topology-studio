qos policy rule action police meter-type shared rule-id
-------------------------------------------------------

**Minimum user role:** operator



Indicate the rule in which the shared policer is defined. 

**Command syntax: rule-id [rule-id]**

**Command mode:** config

**Hierarchies**

- qos policy rule action police meter-type shared

**Note**

- Validate that rule references include a policer definition

- Validate that only rules within the same policy can be referenced

**Parameter table**

+-----------+------------------------------------------------+-------+---------+
| Parameter | Description                                    | Range | Default |
+===========+================================================+=======+=========+
| rule-id   | Reference a meter defined in a different rule. | \-    | \-      |
+-----------+------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type shared
    dnRouter(cfg-action-police-shared)# rule-id 4


**Removing Configuration**

To remove the policer shared rule id:
::

    dnRouter(cfg-action-police-shared)# no rule-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
