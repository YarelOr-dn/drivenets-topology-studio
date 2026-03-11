qos policy rule action police meter-type shared
-----------------------------------------------

**Minimum user role:** operator

To configure an ingress shared meter traffic policing action:

**Command syntax: meter-type shared**

**Command mode:** config

**Hierarchies**

- qos policy rule action police

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-policy-myPolicy1-rule-1-action)# police
    dnRouter(cfg-rule-1-action-police)# meter-type shared


**Removing Configuration**

To remove the meter-type:
::

    dnRouter(cfg-myPolicy1-rule-1-action-police)# no meter-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
