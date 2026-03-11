show qos hardware-utilization - supported in v11.1 - will be moved to show resources 
-------------------------------------------------------------------------------------

**Command syntax: show qos hardware-utilization**

**Description:** show utilization of different QoS components in the system

**CLI example:**
::

	dnRouter# show qos hardware-utilization
	
	Core 0 HBM utilization: 20Gb/24Gb (83.3%)
	Core 1 HBM utilization: 16Gb/24Gb (75%)
	
	Configured VOQs: 600
	Configured WRED profiles: 8/32 (25%)
	Configured WRED profile quatrets: 2/8 (25%)
	Configured Rate class profiles: 16/64 (25%)
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** show utilization of different QoS components in the system

**Parameter table:**

+-----------------------------------+-------------------------------------------------------+---------------+
| Parameter                         | Meaning                                               | Default value |
+===================================+=======================================================+===============+
| HBM utilization                   | Queue DRAM resourses of guaranteed queue size         |               |
+-----------------------------------+-------------------------------------------------------+---------------+
| Configured VOQs                   | User configured VOQs total number per system          |               |
+-----------------------------------+-------------------------------------------------------+---------------+
| Configured WRED profiles          | User configured WRED profiles total number per system | 0             |
+-----------------------------------+-------------------------------------------------------+---------------+
| Configured WRED profiles quatrets | System assigned WRED profiles quatrets per system     | 0             |
+-----------------------------------+-------------------------------------------------------+---------------+
| Configured Rate class profiles    | System assigned rate class profiles per system        |               |
+-----------------------------------+-------------------------------------------------------+---------------+
