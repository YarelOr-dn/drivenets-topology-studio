protocols segment-routing mpls auto-policy timers delete-delay
--------------------------------------------------------------

**Minimum user role:** operator

The global delete delay timer serves as a retention mechanism to minimize flapping and free resources for policies created with SR-TE auto policy templates.
Once the last route associated with a given [NH, color] is withdrawn from BGP, then the delay-timer will start. Upon its expiration when there are no more applicable routes, the auto policy will be deleted automatically.

To configure the global SR-TE auto policy delete delay timer:


**Command syntax: delete-delay [delete-delay]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy timers

**Note**
- Once the delay timer starts and until it expires, the auto policy state is managed per the SR-TE policy state machine as any other policy.

**Parameter table**

+--------------+---------------------------------------------------+---------+---------+
| Parameter    | Description                                       | Range   | Default |
+==============+===================================================+=========+=========+
| delete-delay | Global timer to trigger deletion of auto-policies | 0-86400 | 120     |
+--------------+---------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# timers
    dnRouter(cfg-mpls-auto-policy-timers)# delete-delay 300


**Removing Configuration**

To revert the SR-TE auto policy global delete delay timer to its default value:
::

    dnRouter(cfg-mpls-auto-policy-timers)# no delete-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
