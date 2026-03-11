show services twamp
-------------------

**Minimum user role:** viewer

To display the TWAMP configuration:

**Command syntax: show services twamp** vrf [vrf-name]

**Command mode:** operational



..
	**Internal Note**

	- TWAMP current configuration

	- using 'vrf' optional knob will allow to filter output per specified VRF


**Example**
::

	dnRouter# show services twamp

	TWAMP Admin-state: Enabled
	Mode: Unauthenticated
	Maximum connections: 1000
	Maximum sessions: 1000

	Ports
	  Control source port: 862
	  Data source port range: 10000-20000
	  Data destination port range: 10000-20000

	Timers
	  Session timeout: 900 seconds
	  Server timeout: 900 seconds

	VRF: default
		source-interface: lo1
		Client List
	  		Client list type: deny
	  		Client list networks:
				1.2.3.0/24
				1.2.4.0/24

	VRF: MyVrf_1
		source-interface: lo2
		Client List
	  		Client list type: deny
	  		Client list networks:
				1.2.3.0/24
				1.2.4.0/24
				2001:608::/32


	dnRouter# show services twamp vrf MyVrf_1

	TWAMP Admin-state: Enabled
	Mode: Unauthenticated
	Maximum connections: 1000
	Maximum sessions: 1000

	Ports
	  Control source port: 862
	  Data source port range: 10000-20000
	  Data destination port range: 10000-20000

	Timers
	  Session timeout: 900 seconds
	  Server timeout: 900 seconds

	VRF: MyVrf_1
		source-interface: lo2
		Client List
	  		Client list type: deny
	  		Client list networks:
				1.2.3.0/24
				1.2.4.0/24
				2001:608::/32


.. **Help line:** Displays Simple TWAMP global configuration

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 5.1.0   | Command introduced                 |
+---------+------------------------------------+
| 6.0     | updated the command output         |
+---------+------------------------------------+
| 9.0     | TWAMP not supported                |
+---------+------------------------------------+
| 11.2    | Command re-introduced              |
+---------+------------------------------------+
| 16.2    | Added VRF information              |
+---------+------------------------------------+
