system event-manager
--------------------

**Minimum user role:** admin

To enter the event-manager configuration level:

**Command syntax: event-manager**

**Command mode:** config

**Hierarchies**

- system event-manager


**Note**

- Up to five policies, from all types, can be in admin-state "enabled" simultaneously

- Notice the change in prompt

 .. - event-policy - policy that will be executed upon matching trigger of registered system event.

     - periodic-policy - a recurrent policy according to the scheduled configuration, with limited execution time.

     - generic-policy - policy that will be executed only once and unlimited in execution time.

     - up-to 5 policies can be in admin-state "enabled" at the same time, from all policy types.

    -  there is no "no command".


**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# event-manager
    dnRouter(cfg-system-event-manager)#


.. **Help line:** configure the event-manager functionality.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

