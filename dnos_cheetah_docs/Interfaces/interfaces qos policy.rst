interfaces qos policy direction
-------------------------------

**Minimum user role:** operator

After you have a policy set up, you need to attach it to an interface. To attach a QoS policy to an interface:

**Command syntax: qos policy [policy-name] direction [direction]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| policy-name | Specify the name of an existing policy that you want to attach to the interface. | | string         | \-      |
|             | If the policy does not exist in the database, an error is displayed.             | | length 1-255   |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| direction   | Specify the direction of the traffic to which the policy will apply.             | | in             | \-      |
|             |                                                                                  | | out            |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# qos policy myQoSPolicy1 direction out
    dnRouter(cfg-if-ge100-0/0/0)# qos policy myQoSPolicy2 direction in


**Removing Configuration**

To remove the policy from the interface:
::

    dnRouter(cfg-if-ge100-0/0/0)# no qos policy

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 9.0     | Not supported in this version.                                     |
+---------+--------------------------------------------------------------------+
| 11.2    | Command re-introduced                                              |
+---------+--------------------------------------------------------------------+
