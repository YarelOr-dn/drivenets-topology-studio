system event-manager event-policy event trigger-condition
---------------------------------------------------------

**Minimum user role:** admin

Use this to configure the event attributes and conditions that will trigger the policy.

**Command syntax: trigger-condition [condition]** [event-count]

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- notice the change in prompt

.. - *trigger-condition -* ON, once the event received and the event-count reached.

    - no command returns to default value.

**Parameter table**

+-------------+-----------------------------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                                       | Range  | Default |
+=============+===================================================================================+========+=========+
| condition   | The policy is executed when the number of matching                                |        |         | 
|             | events received equals event-count                                                | \-     | On      |
+-------------+-----------------------------------------------------------------------------------+--------+---------+
| event-count | The number of matching system events that must be received to trigger the policy  | 1..100 | 1       |
+-------------+-----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# trigger-condition on 10
    dnRouter(cfg-policy-test-event)#

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-policy-test-event)# no trigger-condition

.. **Help line:** configures when the event-policy will be executed.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


