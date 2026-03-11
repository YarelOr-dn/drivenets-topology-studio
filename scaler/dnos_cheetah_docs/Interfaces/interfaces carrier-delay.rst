interfaces carrier-delay
------------------------

**Minimum user role:** operator

Flapping interfaces may lead to adjacency failures on LDP and IGP protocols, which may dramatically affect the network convergence time and performance. Carrier Delay enables to delay the advertisement of link state change notifications. When the link state changes, a carrier-delay timer is triggered. While the timer is running, any subsequent link state change is ignored. When the timer expires, if the interface has not returned to its original link state, then the router will advertise the link state change. This allows the control protocols to stabilize in case of a flapping link.

The carrier delay feature supports delay for link up and link down notifications.

To configure carrier-delay, use one of the following commands:

**Command syntax: carrier-delay {up [up-time], down [down-time]}**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to all physical interfaces, including breakout.

- Link state change notifications are not issued during the timer countdown; however, the suppressed notifications are logged.

- You can set different up and down timers. Setting either timer to 0 disables the carrier delay feature for the specific links state change. For example, if down-time is set to 0, then when the interface state changes from "up" to "down", the change notification will be advertized immediately.

**Parameter table**

+-----------+------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                            | Range    | Default |
+===========+========================================================================+==========+=========+
| up-time   | The amount of time (in milliseconds) to delay link-up notifications.   | 0-120000 | 0       |
+-----------+------------------------------------------------------------------------+----------+---------+
| down-time | The amount of time (in milliseconds) to delay link-down notifications. | 0-60000  | 0       |
+-----------+------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-2/1/1
    dnRouter(cfg-if-ge100-2/1/1)# carrier-delay up 100 down 200

    dnRouter(cfg-if-ge100-2/1/1)# carrier-delay down 100
    dnRouter(cfg-if-ge100-2/1/1)# carrier-delay up 300
    dnRouter(cfg-if-ge100-2/1/1)# carrier-delay down 300 up 200


**Removing Configuration**

To revert the carrier delay configuration to the default value
::

    dnRouter(cfg-if-ge100-2/1/1)# no carrier-delay down

::

    dnRouter(cfg-if-ge100-2/1/1)# no carrier-delay up

::

    dnRouter(cfg-if-ge100-2/1/1)# no carrier-delay

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 6.0     | Command introduced     |
+---------+------------------------+
| 16.1    | Extended up-time range |
+---------+------------------------+
