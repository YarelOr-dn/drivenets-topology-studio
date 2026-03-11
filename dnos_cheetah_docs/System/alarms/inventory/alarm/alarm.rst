system alarms inventory alarm
-----------------------------

**Minimum user role:** operator

To configure the alarm.

**Command syntax: alarm [alarm-type-id] [alarm-type-qualifier]**

**Command mode:** config

**Hierarchies**

- system alarms inventory

**Note**

- Alarms are pre-loaded, new alarms can't be created.

**Parameter table**

+----------------------+----------------------------------------------------+------------------------------+---------+
| Parameter            | Description                                        | Range                        | Default |
+======================+====================================================+==============================+=========+
| alarm-type-id        |  alarm module and alarmm name hierarchy parameters | | dnos-alarms                | \-      |
|                      |                                                    | | communications-alarm       |         |
|                      |                                                    | | quality-of-service-alarm   |         |
|                      |                                                    | | processing-error-alarm     |         |
|                      |                                                    | | equipment-alarm            |         |
|                      |                                                    | | environmental-alarm        |         |
|                      |                                                    | | bfd                        |         |
|                      |                                                    | | bgp                        |         |
|                      |                                                    | | efm-oam                    |         |
|                      |                                                    | | management                 |         |
|                      |                                                    | | isis                       |         |
|                      |                                                    | | pcep                       |         |
|                      |                                                    | | l2vpn                      |         |
|                      |                                                    | | aaa                        |         |
|                      |                                                    | | rib                        |         |
|                      |                                                    | | segment-routing            |         |
|                      |                                                    | | static-route               |         |
|                      |                                                    | | ldp                        |         |
|                      |                                                    | | rsvp                       |         |
|                      |                                                    | | fib-manager                |         |
|                      |                                                    | | transaction                |         |
|                      |                                                    | | interfaces                 |         |
|                      |                                                    | | lacp                       |         |
|                      |                                                    | | system                     |         |
|                      |                                                    | | diagnostics                |         |
|                      |                                                    | | platform                   |         |
+----------------------+----------------------------------------------------+------------------------------+---------+
| alarm-type-qualifier | The alarm name                                     | \-                           | \-      |
+----------------------+----------------------------------------------------+------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# inventory
    dnRouter(cfg-system-alarms-inventory)# alarm <alarm-module> <alarm-name>
    dnRouter(cfg-alarms-inventory-alarm)#


**Removing Configuration**

To delete the configuration changes.
::

    dnRouter(cfg-system-alarms-inventory)# no alarm

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 18.0    | Command introduced       |
+---------+--------------------------+
| 19.10   | Added transaction module |
+---------+--------------------------+
