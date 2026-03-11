qos policy rule action queue forwarding-class df wred-profile
-------------------------------------------------------------

**Minimum user role:** operator

To attach an existing profile to a specific queue:

**Command syntax: wred-profile [wred-profile]**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class df

**Parameter table**

+--------------+----------------------------------+------------------+---------+
| Parameter    | Description                      | Range            | Default |
+==============+==================================+==================+=========+
| wred-profile | References the wred-profile name | | string         | \-      |
|              |                                  | | length 1-255   |         |
+--------------+----------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# af
    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# wred-profile my_profile


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# no wred-profile

**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 11.4    | Command introduced                                       |
+---------+----------------------------------------------------------+
| 15.1    | Added support for hp, ef and super-ef forwarding classes |
+---------+----------------------------------------------------------+
