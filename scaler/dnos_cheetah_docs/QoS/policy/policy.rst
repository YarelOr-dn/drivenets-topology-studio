qos policy
----------

**Minimum user role:** operator

A QoS policy is a set of rules and is identified by a unique name.

To create a QoS policy:

**Command syntax: policy [policy]**

**Command mode:** config

**Hierarchies**

- qos

**Note**

- You cannot remove a policy if it is attached to an interface.

- A policy must include a rule with an action. The action can be configured on any rule, including the default.

**Parameter table**

+-----------+----------------------------------------------+------------------+---------+
| Parameter | Description                                  | Range            | Default |
+===========+==============================================+==================+=========+
| policy    | References the configured name of the policy | | string         | \-      |
|           |                                              | | length 1-255   |         |
+-----------+----------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1


**Removing Configuration**

To remove the policy
::

    dnRouter(cfg-qos)# no policy MyQoSPolicy1

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
