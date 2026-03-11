show services mpls-oam
----------------------

**Minimum user role:** viewer

To display MPLS-OAM service information for RSVP tunnels:

**Command syntax: show services mpls-oam** {profile [profile-name] \| tunnel-name [tunnel-name] \| auto-mesh [template-name] \| auto-bypass}

**Command mode:** operational



**Parameter table**

+---------------+---------------------------------------------------------------------+--------+---------+
| Parameter     | Description                                                         | Range  | Default |
+===============+=====================================================================+========+=========+
| profile-name  | Optionally display information by profile                           | String | \-      |
+---------------+---------------------------------------------------------------------+--------+---------+
| tunnel-name   | Optionally filter the displayed information by tunnel               | String | \-      |
+---------------+---------------------------------------------------------------------+--------+---------+
| template-name | Optionally filter the displayed information by auto-mesh template   | String | \-      |
+---------------+---------------------------------------------------------------------+--------+---------+
| Auto-bypass   | Optionally filter the displayed information for auto-bypass tunnels | String | \-      |
+---------------+---------------------------------------------------------------------+--------+---------+

For each tunnel, the following information is displayed:

+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Parameter         | Description                                                                                                                                                    | Range                  |
+===================+================================================================================================================================================================+========================+
| Tunnel name       | The name of the tunnel.                                                                                                                                        | String                 |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| MPLS-OAM profile  | The name of the profile associated with the tunnel                                                                                                             | String                 |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Profile state     | Indicates the current state of the profile                                                                                                                     | Active                 |
|                   |                                                                                                                                                                | Disabled               |
|                   |                                                                                                                                                                | Inactive (tunnel down) |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Last probe result | Displays the result of the last probe                                                                                                                          | Succeeded              |
|                   |                                                                                                                                                                | Failed                 |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Probe count       | The number of probes tested in the specific MPLS-OAM service                                                                                                   | Integer                |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Probe loss        | The number of failed probes in the specific MPLS-OAM service. A failed probe is one for which none of the MPLS echo requests have returned a successful reply. | Integer                |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Packet count      | The number of MPLS echo requests that were sent in the specific MPLS-OAM service                                                                               | Integer                |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Packet loss       | The number of MPLS echo requests in the specific MPLS-OAM service that have not received a successful reply                                                    | Integer                |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Threshold reached | The number of times that a threshold was crossed resulting in a system event being generated                                                                   | Integer                |
+-------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+

**Example**
::

	dnRouter# show services mpls-oam
	Tunnel Name
	Mpls-oam profile
	Profile state
	Last probe result
	Probe count
	Probe loss
	Packet count
	Packet loss
	Threshold reached
	tunnel_1
	COS_1
	active
	failed
	3460
	2
	17300
	10
	0
	tunnel_2
	COS_1
	active
	succeeded
	144
	0
	720
	0
	0
	tunnel_3
	COS_2
	disabled
	-
	-
	-
	-
	-
	0
	tunnel_4
	COS_1
	inactive (tunnel down)
	failed
	8
	2
	40
	10
	1
	
	dnRouter# show services mpls-oam tunnel-name tunnel_1
	Tunnel Name
	Mpls-oam profile
	Profile state
	Last probe result
	Probe count
	Probe loss
	Packet count
	Packet loss
	Threshold reached
	tunnel_1
	COS_1
	active
	failed
	3460
	2
	17300
	10
	0
	
	
	dnRouter# show services mpls-oam profile COS_1
	Tunnel Name
	Mpls-oam profile
	Profile state
	Last probe result
	Probe count
	Probe loss
	Packet count
	Packet loss
	Threshold reached
	tunnel_1
	COS_1
	active
	failed
	3460
	2
	17300
	10
	0
	tunnel_2
	COS_1
	active
	succeeded
	144
	0
	720
	0
	0
	tunnel_4
	COS_1
	inactive (tunnel down)
	failed
	8
	2
	40
	10
	1
	
	


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
