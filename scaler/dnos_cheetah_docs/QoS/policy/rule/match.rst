qos policy rule match traffic-class
-----------------------------------

**Minimum user role:** operator

Each rule (except the default rule) has matching criteria against which traffic is checked. If the traffic meets the matching criteria, then actions are applied on the traffic. The matching criteria are defined in traffic-class maps.

For each rule, you need to specify the traffic-class map using the following command:

**Command syntax: match traffic-class [traffic-class-map]**

**Command mode:** config

**Hierarchies**

- qos policy rule

**Parameter table**

+-------------------+--------------------------------------+------------------+---------+
| Parameter         | Description                          | Range            | Default |
+===================+======================================+==================+=========+
| traffic-class-map | References the classifier entry name | | string         | \-      |
|                   |                                      | | length 1-255   |         |
+-------------------+--------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule 1
    dnRouter(cfg-policy-MyQoSPOlicy1-rule-1)# match traffic-class myTrafficClassMap


**Removing Configuration**

To remove the matching criterion
::

    dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no match traffic-class

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
