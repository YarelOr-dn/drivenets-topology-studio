qos policy rule action queue forwarding-class super-ef ecn-profile
------------------------------------------------------------------

**Minimum user role:** operator

To attach an existing profile to a specific queue:

**Command syntax: ecn-profile [ecn-profile]**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class super-ef

**Parameter table**

+-------------+---------------------------------+------------------+---------+
| Parameter   | Description                     | Range            | Default |
+=============+=================================+==================+=========+
| ecn-profile | References the ecn-profile name | | string         | \-      |
|             |                                 | | length 1-255   |         |
+-------------+---------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# sef
    dnRouter(cfg-myPolicy1-rule-1-action-queue-sef)# ecn-profile my_profile


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-sef)# no ecn-profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
