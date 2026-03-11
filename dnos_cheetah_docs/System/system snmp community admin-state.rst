system snmp community admin-state
---------------------------------

**Minimum user role:** operator

Configure system snmp community admin state.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Note:**

No command reverts the admin-state configuration to its default value

Validation: fail commit if more than one in-band management non-default VRF is configured with admin-state “enabled” knob.

**Parameter table:**

+--------------+------------------------+---------------+
| Parameter    | Values                 | Default value |
+==============+========================+===============+
| admin-state  | enabled/disabled       | enabled       |
+--------------+------------------------+---------------+

**Example:**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
    dnRouter(cfg-system-snmp-community)# admin-state disabled

    dnRouter(cfg-system-snmp)# community MyPrivateSnmpCommunity vrf mgmt0
    dnRouter(cfg-system-snmp-community)# admin-state disabled

    dnRouter(cfg-system-snmp)# community MyPublicSnmpCommunity vrf my_vrf
    dnRouter(cfg-system-snmp-community)# admin-state enabled


**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 16.2    | Command introduced                    |
+---------+---------------------------------------+



