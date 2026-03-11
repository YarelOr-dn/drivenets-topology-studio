interfaces carrier-delay on-startup interval
--------------------------------------------

**Minimum user role:** operator

Use this command on network interfaces to delay their operational status change to "up" when the interface carrier is brought up as a result of any of the following manual operations or events:

- A manual cold or warm system restart (see "request system restart"):

  -	"request system restart"
  -	"request system restart warm"
- A manual cold and warm restart of a specific NCP (see "request system restart"):

  - "request system restart ncp n"
  - "request system restart ncp n warm"
- A manual restart of a container or process:

  - "request system container restart ncp 0 datapath" (see "request system container restart")
  - "request system process restart ncp 0 datapath wb_agent" (see "request system process restart")
- A manual change of the NCP admin-state to "disabled" and back to "enabled" (see "system ncp admin-state")
- After recovering from an NCP system-down state.

To configure the delay time:

**Command syntax: carrier-delay on-startup interval [interval]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to all physical interfaces.

- When interval is set to 0, carrier delay on-startup is disabled.

- If the interval is set while the interface carrier-delay on-startup timer has not yet expired, the new interval value will apply to the next carrier-delay on-startup event.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                      | Range  | Default |
+===========+==================================================================================+========+=========+
| interval  | The amount of time (in seconds) that the system will wait after the interface is | 0-1800 | 0       |
|           | back up before changing its operational state to "up".                           |        |         |
+-----------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-2/1/1
    dnRouter(cfg-if-ge100-2/1/1)# carrier-delay on-startup interval 1200

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/9
    dnRouter(cfg-if-ge400-0/0/9)# carrier-delay on-startup interval 800


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-2/1/1)# no carrier-delay on-startup interval

::

    dnRouter(cfg-if-ge100-2/1/1)# no carrier-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
