show rsvp tunnels auto-bw
-------------------------

**Minimum user role:** viewer

To display RSVP tunnels auto-bandwidth information:



**Command syntax: show rsvp tunnels auto-bw**

**Command mode:** operational



**Note**

Displays the following information for all head tunnels in UP state for which the auto-bw feature is enabled:

- req BW - The bandwidth requested by the current active LSP

- Auto-BW req BW - Auto-bandwidth Last requested BW

- Max Avg-rate - The highest avg-rate sample in the current adjustment interval period

- Overflow - Auto-bandwidth tunnel overflow setting

- Underflow - Auto-bandwidth tunnel underflow setting

- Re-adjust - The remaining time for auto-bandwidth re-adjustment according to the tunnel adjust interval

- Name - The tunnel name.



**Example**
::

	dnRouter# show rsvp tunnels auto-bw

	Destination     req BW        Auto-BW req BW  Max Avg-rate   Overflow     Underflow   Re-adjust    Name
	                (kbps)        (kbps)          (kbps)         (kbps)       (kbps)      (HH:MM:SS)
	--------------------------------------------------------------------------------------------------------------------------
	100.19.19.19    11            3012352         3011993        300000       300000      00:06:04     auto_tunnel_C2_AR1_R13_C2_AR2_R19_Devtest_CORE_Routers_Default_1
	100.19.19.19    46            46              44             300000       300000      00:01:16     auto_tunnel_C2_AR1_R13_C2_AR2_R19_Devtest_CORE_Routers_Priority_2
	100.41.41.41    100           100             75             100000       100000      00:00:17     To-R41-P

.. **Help line:** Displays rsvp tunnel auto-bandwidth information

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+


