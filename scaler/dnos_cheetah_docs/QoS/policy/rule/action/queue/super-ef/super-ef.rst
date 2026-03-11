qos policy rule action queue forwarding-class super-ef
------------------------------------------------------

**Minimum user role:** operator

To configure the super-ef queue forwarding-class for the matched traffic.

**Command syntax: forwarding-class super-ef**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue

**Note**

- Only one queue action for a super-ef forwarding-class is allowed per policy.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# super-ef


**Removing Configuration**

To remove the queue configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue)# no super-ef

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
