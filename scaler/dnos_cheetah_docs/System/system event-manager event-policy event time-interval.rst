system event-manager event-policy event time-interval
-----------------------------------------------------

**Minimum user role:** admin

Use this command to configure the time frame within which the registered system-events must get to the triggered condition.

**Command syntax: time-interval [interval]**

**Command mode:** config

**Hierarchies**

- system event-manager event-policy


**Note**

- Notice the change in prompt.

.. - *time-interval -* the duration of time the event-count needs to be reached in order to execute the policy. "0" is used as infinite value.

    - no command returns to default value.

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------+--------------------------+---------+
| Parameter | Description                                                                                                        | Range                    | Default |
+===========+====================================================================================================================+==========================+=========+
| interval  | The duration of time the event-count must be reached for the policy to be executed. "0" is used as infinite value. | 0 | 60..604800 (seconds) | 0       |
+-----------+--------------------------------------------------------------------------------------------------------------------+--------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# time-interval 300
    dnRouter(cfg-policy-test-event)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-policy-test-event)# no time-interval

.. **Help line:** configure the time interval in seconds.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


