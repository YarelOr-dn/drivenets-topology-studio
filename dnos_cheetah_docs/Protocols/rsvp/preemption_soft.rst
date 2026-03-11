protocols rsvp preemption soft
------------------------------

**Minimum user role:** operator

When bandwidth is insufficient to handle all RSVP tunnels (for example when a new tunnel with bandwidth reservation needs to be installed, or one of the members of a bundle interface fails), you can control the preemption of one or more existing RSVP bandwidth reservations to accommodate a higher priority reservation. The preemption will occur in make-before-break fashion, such that the lower priority tunnel is maintained until the alternative higher priority tunnel is successfully established.
You can choose between two preemption types:

- Hard: the device tears down a preempted LSP first, signals a new path, and then reestablishes the LSP over the new path. In the interval between the time that the LSP is taken down and the new LSP is established, any traffic attempting to use the LSP is lost.

- Soft: the device first attempts to find a new path for the preempted LSP before tearing down the old path to prevent traffic loss. During soft preemption, the two LSPs with their corresponding bandwidth requirements are used until the original path is torn down. 

When enabled, tunnel changes will be applied only if the new tunnel is created successfully. When preemption is required, the least number of tunnels will be preempted in order to satisfy the new bandwidth requirement.

To configure preemption:

**Command syntax: preemption soft** timeout [timeout]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -timeout - can only be set for type 'soft'

.. -'no preemption soft timeout' - return timeout to default value

.. -'no preemption' - return to default preemption settings (soft) with default timeout value

- Preemption affects transit routers.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                      | Range  | Default |
+===========+==================================================================================+========+=========+
| timeout   | maximum time for trying to establish alternate tunnel before primary tunnel is   | 30-300 | 30      |
|           | preempted                                                                        |        |         |
+-----------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# preemption soft timeout 40

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# preemption hard


**Removing Configuration**

To revert to the default timeout value:
::

    dnRouter(cfg-protocols-rsvp-mmb)# no preemption soft timeout

To revert to the default preemption type (and reverts the timeout to default):
::

    dnRouter(cfg-protocols-rsvp-mmb)# no preemption

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
