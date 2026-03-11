system snmp trap-server admin-state
-----------------------------------

**Minimum user role:** operator

Configure system snmp trap-server admin state.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Note:**

no command reverts the admin-state configuration to its default value

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
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# admin-state enabled
	
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf my_vrf
	dnRouter(cfg-system-snmp-trap-server)# admin-state disabled
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.5 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# admin-state disabled
	


**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 16.2    | Command introduced                    |
+---------+---------------------------------------+


