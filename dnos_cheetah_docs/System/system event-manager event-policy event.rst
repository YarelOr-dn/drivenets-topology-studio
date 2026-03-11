system event-manager event-policy event
---------------------------------------

**Minimum user role:** admin

Use this command to configure the attributes and conditions which triggers the policy. Up to five scripts can run simultaneously.

**Command syntax: event [event-name]** {attribute [event-attribute] \| trigger-condition [condition] \| time-interval [interval]}

**Command mode:** config

**Hierarchies**

- system event-manager event-policy event

**Note**

- A policy script can be used by several named policies as long as the system-events are different.

- Notice the change in prompt.

.. - *trigger-condition -* ON, once the event received and the event-count reached.

    - *time-interval -* the duration of time the event-count needs to be reached in order to execute the policy. "0" is used as infinite value.

    - no command removes a specific event entry, upon removal all running policies will continue to run until termination.

    Validation:

    - Policy-script can be used by several policy-names as long as the system-events are different.

    - Only up to 5 policies can be in admin-state "enabled" in the same time.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| Parameter       | Description                                                                                                        | Range                     | Default |
+=================+====================================================================================================================+===========================+=========+
| event-name      | The system event name the script needs to register                                                                 | string (lower case only)  | \-      |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| event-attribute | A variable name to match in the system event                                                                       | string                    | \-      |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| condition       | Once the event-count has been reached, the condition when the policy is triggered                                  | \-                        | On      |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+
| interval        | The duration of time the event-count must be reached for the policy to be executed. "0" is used as infinite value. | 0 | 60.. 604800 (seconds) | 0       |
+-----------------+--------------------------------------------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# attribute new-state
    dnRouter(cfg-policy-test-event)#
    dnRouter(cfg-policy-test-event)# trigger-condition on
    dnRouter(cfg-policy-test-event)#
    dnRouter(cfg-policy-test-event)# time-interval 300
    dnRouter(cfg-policy-test-event)#



**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-event-policy-test)# no event if_link_state_change_down

.. **Help line:** configure the event-policy parameters.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

