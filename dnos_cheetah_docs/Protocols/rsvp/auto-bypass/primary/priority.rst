protocols rsvp auto-bypass primary priority setup hold
------------------------------------------------------

**Minimum user role:** operator

Tunnel priority allows you to configure the reservation setup and hold priority:

- Setup priority: the priority used when signaling an LSP for this tunnel to determine which existing tunnels can be preempted. A lower value indicates a higher priority. An LSP -  preempt any LSP with a lower priority.

- Hold priority: the priority used to determine if the LSP can be preempted by other signaled LSPs. A lower value indicates a higher priority. The higher the hold priority, the LSP is less likely to give up its reservation (i.e. is less likely to be preempted by a higher priority LSP).

If there is not enough bandwidth to create a new tunnel, the source (head) router will compare the setup priority of the new tunnel to the hold priority of existing tunnels to decide if to preempt an existing tunnel.

To configure the tunnel priority:

**Command syntax: priority setup [setup] hold [hold]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass primary
- protocols rsvp tunnel primary
- protocols rsvp tunnel bypass primary
- protocols rsvp auto-mesh tunnel-template primary

**Note**
- The value of hold-priority must be ≤ setup-priority.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| setup     | priority used when signaling an LSP for this tunnel to determine which existing  | 0-7   | \-      |
|           | tunnels can be preempted                                                         |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+
| hold      | priority associated with an LSP for this tunnel to determine if it should be     | 0-7   | \-      |
|           | preempted by other LSPs that are being signaled                                  |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# priority setup 3 hold 3

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL2
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# priority setup 5 hold 1


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no priority

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 9.0     | Command introduced                                 |
+---------+----------------------------------------------------+
| 10.0    | Added support for bypass tunnels (manual and auto) |
+---------+----------------------------------------------------+
