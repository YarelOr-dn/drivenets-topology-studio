system alarms shelve rule module
--------------------------------

**Minimum user role:** operator

To configure the shelve policy rule matching the alarm component module.

**Command syntax: module [alarm-type-id]** alarm [alarm-type-qualifier]

**Command mode:** config

**Hierarchies**

- system alarms shelve rule

**Note**
Alarms will be matched by the alarm component module.

- A specific alarm or module can be listed under one shelve only.
  Error: The alarm already exists in <shelve-name>.

- In case a module is shelved, all alarms that belong to that module will be shelved as well.

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+------------------------------+---------+
| Parameter            | Description                                                                      | Range                        | Default |
+======================+==================================================================================+==============================+=========+
| alarm-type-id        | Shelve all alarms that have an 'alarm-type-id' that is equal to or derived from  | | dnos-alarms                | \-      |
|                      | the given 'alarm-type-id'.                                                       | | communications-alarm       |         |
|                      |                                                                                  | | quality-of-service-alarm   |         |
|                      |                                                                                  | | processing-error-alarm     |         |
|                      |                                                                                  | | equipment-alarm            |         |
|                      |                                                                                  | | environmental-alarm        |         |
|                      |                                                                                  | | bfd                        |         |
|                      |                                                                                  | | bgp                        |         |
|                      |                                                                                  | | efm-oam                    |         |
|                      |                                                                                  | | management                 |         |
|                      |                                                                                  | | isis                       |         |
|                      |                                                                                  | | pcep                       |         |
|                      |                                                                                  | | l2vpn                      |         |
|                      |                                                                                  | | aaa                        |         |
|                      |                                                                                  | | rib                        |         |
|                      |                                                                                  | | segment-routing            |         |
|                      |                                                                                  | | static-route               |         |
|                      |                                                                                  | | ldp                        |         |
|                      |                                                                                  | | rsvp                       |         |
|                      |                                                                                  | | fib-manager                |         |
|                      |                                                                                  | | transaction                |         |
|                      |                                                                                  | | interfaces                 |         |
|                      |                                                                                  | | lacp                       |         |
|                      |                                                                                  | | system                     |         |
|                      |                                                                                  | | diagnostics                |         |
|                      |                                                                                  | | platform                   |         |
+----------------------+----------------------------------------------------------------------------------+------------------------------+---------+
| alarm-type-qualifier | The optionally dynamically defined alarm type identifier for this possible       | \-                           | \-      |
|                      | alarm.                                                                           |                              |         |
+----------------------+----------------------------------------------------------------------------------+------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# shelve my_shelve
    dnRouter(cfg-system-alarms-shelve)# rule 8
    dnRouter(cfg-alarms-shelve-rule)# module pcep

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# shelve my_shelve
    dnRouter(cfg-system-alarms-shelve)# rule 1
    dnRouter(cfg-alarms-shelve-rule)# module platform alarm bfd_micro_bfd_state_down


**Removing Configuration**

To delete the configured module
::

    dnRouter(cfg-alarms-shelve-rule)# no module

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
