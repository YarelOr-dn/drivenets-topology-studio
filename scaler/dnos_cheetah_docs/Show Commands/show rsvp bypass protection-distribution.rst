show rsvp bypass protection-distribution
----------------------------------------

**Minimum user role:** viewer

To display bypass tunnels protected bandwidth and LSP count distribution:

**Command syntax: show rsvp bypass protection-distribution** {destination [destination] protected-interface [interface name] | name [bypass-name] | detail}

**Command mode:** operational



**Note**

- Displays only bypass tunnels that are in UP state (active LSP).

..
	**Internal Note**
	- Display sort order: 1. sort by destination address 2. for all identical destination sort by Protected-IF  3. for all identical Protected-IF sort by ProtectedBw  4. for all identical ProtectedBw sort by Protected-Lsp

	- When displaying info of specific bypass, sort by bandwidth

**Parameter table**

+----------------+------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter      | Description                                                                                                | Range                                              | Default |
+================+============================================================================================================+====================================================+=========+
| destination    | The bypass tunnel destination address                                                                      | A.B.C.D                                            | \-      |
+----------------+------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| interface-name | The name of the interface for which the tunnel will provide protection                                     | configured rsvp interface name                     |         |
|                |                                                                                                            | ge{/10/25/40/100}-X/Y/Z                            |         |
|                |                                                                                                            | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> | \-      |
|                |                                                                                                            | bundle-<bundle-id>                                 |         |
|                |                                                                                                            | bundle-<bundle-id.sub-bundle-id>                   |         |
+----------------+------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| name           | The name of the bypass tunnel. When set, it lists which primary tunnels are protected by the given bypass. | string, bypass tunnel name                         | \-      |
+----------------+------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+

**Example**
::

	dnRouter# show rsvp bypass protection-distribution

	protection-distribution interval: 5min    next: 00:03:28

	Destination     Protected-IF       ProtectedBw [kbps] Protected-Lsp   Name
	--------------------------------------------------------------------------------------------
	3.3.3.3         bundle-1           6                  2               tunnel_bypass_node-bundle-1
	3.3.3.3         bundle-1           4                  2               manual_bypass_node_bundle-1_1
	3.3.3.3         bundle-1           2                  2               manual_bypass_node_bundle-1_2
	2.2.2.2         bundle-4           13                 3               tunnel_bypass_node-bundle-4
	2.2.2.2         bundle-4           6                  2               manual_bypass_node_bundle-4_1
	2.2.2.2         bundle-4           2                  2               manual_bypass_node_bundle-4_1


	dnRouter# show rsvp bypass protection-distribution protected-interface bundle-4

	protection-distribution interval: 5min    next: 00:03:28

	Destination     Protected-IF       ProtectedBw [kbps] Protected-Lsp   Name
	--------------------------------------------------------------------------------------------
	2.2.2.2         bundle-4           13                 3               tunnel_bypass_node-bundle-4
	2.2.2.2         bundle-4           6                  2               manual_bypass_node_bundle-4_1
	2.2.2.2         bundle-4           2                  2               manual_bypass_node_bundle-4_1

	dnRouter# show rsvp bypass protection-distribution destination 3.3.3.3 protected-interface bundle-1

	protection-distribution interval: 5min    next: 00:03:28

	Destination     Protected-IF       ProtectedBw [kbps] Protected-Lsp   Name
	--------------------------------------------------------------------------------------------
	3.3.3.3         bundle-1           6                  2               tunnel_bypass_node-bundle-1
	3.3.3.3         bundle-1           4                  2               manual_bypass_node_bundle-1_1
	3.3.3.3         bundle-1           2                  2               manual_bypass_node_bundle-1_2


	dnRouter# show rsvp bypass protection-distribution name manual_bypass_node_bundle-1_2

	Protection summary for bypass tunnel:   manual_bypass_node_bundle-1_2

	Total Protected bandwidth: 60kbps
	Number of LSP protected: 51
	Backup bandwidth: any-class, unlimited

	Protected LSPs:
	Destination     Source          Role    Bandwidth [kbps]    Name
	-----------------------------------------------------------------------------------------
	6.19.0.1        100.13.13.13    head    30                  auto_tunnel_C2_AR1_R13_R19-RUR1_R19_Scale_293
	6.19.0.2        100.13.13.13    head    10                  auto_tunnel_C2_AR1_R13_R19-RUR2_R19_Scale_248
	6.19.0.3        100.13.13.13    head    7                   auto_tunnel_C2_AR1_R13_R19-RUR3_R19_Scale_344
	6.19.0.4        100.13.13.13    head    5                   auto_tunnel_C2_AR1_R13_R19-RUR4_R19_Scale_208
	6.19.0.5        100.13.13.13    head    5                   auto_tunnel_C2_AR1_R13_R19-RUR5_R19_Scale_241
	6.19.0.6        100.13.13.13    head    3                   auto_tunnel_C2_AR1_R13_R19-RUR6_R19_Scale_360


	dnRouter# show rsvp bypass protection-distribution detail

	Protection summary for bypass tunnel:   manual_bypass_node_bundle-1_2

	Total Protected bandwidth: 60kbps
	Number of LSP protected: 4
	Backup bandwidth: any-class, unlimited

	Protected LSPs:
	Destination     Source          Role    Bandwidth [kbps]    Name
	-----------------------------------------------------------------------------------------
	6.19.0.1        100.13.13.13    head    30                  auto_tunnel_C2_AR1_R13_R19-RUR1_R19_Scale_293
	6.19.0.2        100.13.13.13    head    10                  auto_tunnel_C2_AR1_R13_R19-RUR2_R19_Scale_248
	6.19.0.3        100.13.13.13    head    7                   auto_tunnel_C2_AR1_R13_R19-RUR3_R19_Scale_344
	6.19.0.4        100.13.13.13    head    5                   auto_tunnel_C2_AR1_R13_R19-RUR4_R19_Scale_208


 	Protection summary for bypass tunnel:   tunnel_bypass_node-bundle-2

	Total Protected bandwidth: 60kbps
	Number of LSP protected: 2
	Backup bandwidth: any-class, unlimited

	Protected LSPs:
	Destination     Source          Role    Bandwidth [kbps]    Name
	-----------------------------------------------------------------------------------------
	192.168.1.1     192.168.10.2    transit 30                  auto_tunnel_CORE1_CORE9_3
	192.168.19.91   192.168.10.2    transit 10                  auto_tunnel_CORE1_ABR1_2


	Protection summary for bypass tunnel:   tunnel_bypass_node-bundle-4

	Total Protected bandwidth: 60kbps
	Number of LSP protected: 3
	Backup bandwidth: any-class, unlimited

	Protected LSPs:
	...

.. **Help line:** Displays bypass tunnels protected bandwidth distribution

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
