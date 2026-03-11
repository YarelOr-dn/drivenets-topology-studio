services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check fault-alarm lowest-priority-defect
----------------------------------------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the fault alarm reporting:

**Command syntax: fault-alarm lowest-priority-defect [lowest-priority-defect]** defect-delay [alarm-timer] clear-delay [reset-timer]

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+------------------------+----------------------------------------------------------------------+---------------------------+-----------------------+
| Parameter              | Description                                                          | Range                     | Default               |
+========================+======================================================================+===========================+=======================+
| lowest-priority-defect | The lowest priority defect that is allowed to generate fault alarms. | | all-defects             | mac-remote-error-xcon |
|                        |                                                                      | | mac-remote-error-xcon   |                       |
|                        |                                                                      | | remote-error-xcon       |                       |
|                        |                                                                      | | error-xcon              |                       |
|                        |                                                                      | | xcon                    |                       |
|                        |                                                                      | | no-defects              |                       |
+------------------------+----------------------------------------------------------------------+---------------------------+-----------------------+
| alarm-timer            | The time that defect must be present before a Fault Alarm is issued. | 2500-10000                | 2500                  |
+------------------------+----------------------------------------------------------------------+---------------------------+-----------------------+
| reset-timer            | The time that defects must be absent before resetting a Fault Alarm. | 2500-10000                | 10000                 |
+------------------------+----------------------------------------------------------------------+---------------------------+-----------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# continuity-check
    dnRouter(cfg-md-ma-ccm)# fault-alarm lowest-priority-defect mac-remote-error-xcon


**Removing Configuration**

To revert continuity check fault alarm configuration to its default value:
::

    dnRouter(cfg-md-ma-ccm)# no fault-alarm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
