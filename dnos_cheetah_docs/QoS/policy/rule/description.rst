qos policy rule description
---------------------------

**Minimum user role:** operator

You may want to add a meaningful description for the rule. To add a description for the rule:

Make sure that you are within the rule mode (check for the rule ID in the prompt), and use the following command:

**Command syntax: description [rule-descr]**

**Command mode:** config

**Hierarchies**

- qos policy rule

**Parameter table**

+------------+------------------+------------------+---------+
| Parameter  | Description      | Range            | Default |
+============+==================+==================+=========+
| rule-descr | rule description | | string         | \-      |
|            |                  | | length 1-255   |         |
+------------+------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-qos-policy-MyQoSPolicy1)# rule 1
    dnRouter(cfg-policy-MyQoSPolicy1-rule-1)# description "real time service"


**Removing Configuration**

To remove the description
::

    dnRouter(cfg-policy-MyQoSPolicy1-rule-1)# no description

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 5.1.0   | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 6.0     | When moving into different modes, higher mode names are removed |
+---------+-----------------------------------------------------------------+
| 9.0     | QoS not supported                                               |
+---------+-----------------------------------------------------------------+
| 11.2    | Command re-introduced                                           |
+---------+-----------------------------------------------------------------+
