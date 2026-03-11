system event-manager event-policy event attribute
-------------------------------------------------

**Minimum user role:** admin

Use this command to configure the event attributes and matching regex, which will trigger the policy.

**Command syntax: attribute [event-attribute]** match [regex]

**Command mode:** config

**Hierarchies**

- system event-manager event-policy

**Note**

- Notice the change in prompt.

.. - no command removes the attribute and match configuration.


**Parameter table**

+-----------------+-----------------------------------------------------+--------------------+---------+
| Parameter       | Description                                         | Range              | Default |
+=================+=====================================================+====================+=========+
| regex           | A regular expression to match the attribute pattern | regular expression | \-      |
+-----------------+-----------------------------------------------------+--------------------+---------+
| event-attribute | A variable name to match in the system event        | string             | \-      |
+-----------------+-----------------------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)# event-policy test
    dnRouter(cfg-event-policy-test)# event if_link_state_change_down
    dnRouter(cfg-policy-test-event)# attribute new-state match .*down.*
    dnRouter(cfg-policy-test-event)#


**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-test-system-event)# no attribute

.. **Help line:** system event attributes to match with.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


