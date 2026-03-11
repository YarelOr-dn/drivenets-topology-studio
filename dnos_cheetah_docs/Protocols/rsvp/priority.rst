protocols rsvp priority setup hold
----------------------------------

**Minimum user role:** operator

Preemption of an existing LSP is used when there is insufficient bandwidth. Priority determines whether an LSP can be preempted or can preempt another LSP using the following properties:

- Setup priority - determines which tunnels can be preempted. For preemption to occur, the setup priority of the new tunnel must be higher than the setup priority of the existing tunnel.

- Hold priority - determines which LSP should be preempted by other LSPs. A high hold priority means that the LSP is less likely to be preempted (that is, it is less likely to give up its reservation).

To prevent preemption loops (i.e. when two LSPs are allowed to preempt each other), the hold priority must be greater than or equal to the setup priority.
By default, an LSP has a setup priority of 7 (meaning it cannot preempt any other LSP) and a hold priority of 0 (meaning it cannot be preempted by other LSPs), so that preemption does not happen.
To globally configure the tunnels' reservation priority:

**Command syntax: priority setup [setup] hold [hold]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- Hold-priority must be ≥ setup priority to prevent preemption loops.

.. -  must comply [hold-priority] <= [setup-priority]

.. -  no command returns to default priority settings.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| setup     | priority used when signaling an LSP for this tunnel to determine which existing  | 0-7   | 7       |
|           | tunnels can be preempted                                                         |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+
| hold      | priority associated with an LSP for this tunnel to determine if it should be     | 0-7   | 0       |
|           | preempted by other LSPs that are being signaled                                  |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# priority setup 3 hold 3


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
