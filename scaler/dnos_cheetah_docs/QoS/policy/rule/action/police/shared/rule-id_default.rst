qos policy rule action police meter-type shared rule-id default
---------------------------------------------------------------

**Minimum user role:** operator



Indicates the rule in which the shared policer is defined. 

**Command syntax: rule-id default**

**Command mode:** config

**Hierarchies**

- qos policy rule action police meter-type shared

**Note**

- Validate that the rule references includes a policer definition.

- Validate that only rules within the same policy can be referenced.

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
    dnRouter(cfg-action-police-shared)# rule-id default


**Removing Configuration**

To remove the policer shared rule id:
::

    dnRouter(cfg-action-police-shared)# no rule-id default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
