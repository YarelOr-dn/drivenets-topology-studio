qos policy rule action queue forwarding-class df
------------------------------------------------

**Minimum user role:** operator

To configure the df queue forwarding-class for the matched traffic.

**Command syntax: forwarding-class df**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue

**Note**

- Queue action for df forwarding-class is available in rule default only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# df


**Removing Configuration**

To remove the queue configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue)# no df

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
