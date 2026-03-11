system event-manager event-policy policy-iteration
--------------------------------------------------

**Minimum user role:** admin

Use this command to configure the number of times the policy will be executed.

**Command syntax: policy-iteration [iteration]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy 


**Note**

- Notice the change in prompt.

.. - Once the policy executed the policy-iteration number of times the policy will appear in operational-state "inactive".

    - a change in the policy-iteration configuration during policy execution will take effect on the next policy execution.

    - "0" is used as infinite value.

    - no command resets policy-iteration to default, will take effect on next policy execution.

**Parameter table**

+-----------+--------------------------------------------------+-------------+---------+
| Parameter | Description                                      | Range       | Default |
+===========+==================================================+=============+=========+
| iteration | The number of times the policy will be executed. | 0 | 1..1000 | 0       |
|           | "0" is an infinite value                         |             |         |
+-----------+--------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-event-policy-test)# policy-iteration 0
    dnRouter(cfg-event-policy-test)#
    dnRouter(cfg-event-policy-test)# policy-iteration 20
    dnRouter(cfg-event-policy-test)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no policy-iteration

.. **Help line:** configure the number of policy iterations.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


