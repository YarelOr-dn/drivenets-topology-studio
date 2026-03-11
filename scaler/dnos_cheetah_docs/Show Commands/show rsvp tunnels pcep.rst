show rsvp tunnels pcep
----------------------

**Minimum user role:** viewer

To display PCEP delegated tunnel information per LSP:

**Command syntax: show rsvp tunnels pcep** 

**Command mode:** operational


**Notes**

	-	Oper-dlg - delegation operationl state

	 -	No-PCE - tunnels is expected to be delegated but there is no available pce
	 -	delegated - tunnel is delegated to the pce
	 -	not-delegated - tunnels is not delegated.
	 -	not-configured - tunnel is not configured for delegation

	-	PClsp-id - for delegated tunnels, print the PLSP-ID send out in the PCRpt for the given tunnel.
	-	Sticky-ERO - Display tunnel sticky-ero settingsd

**Parameter table**

+-------------+-----------------------------------------------------------------------------+-------------------+
| Parameter   | Description                                                                 | Range             |
+=============+=============================================================================+===================+
| no filter   | Displays all RSVP tunnels.                                                  | \-                |
+-------------+-----------------------------------------------------------------------------+-------------------+

**Example**
::

	dnRouter# show rsvp tunnels pcep

	Legend: * - Make-Before-Break

	Destination     Source          State   Oper-dlg         PClsp-id  Sticky-ERO  Uptime/Downtime  Name
	----------------------------------------------------------------------------------------------------------------------------------
	100.15.15.15    100.16.16.16    down    delegated               3  enabled     40m17s           DELEGATED_TUNNEL_R15
	100.15.15.15    100.16.16.16    down    not-delegated              disabled    40m17s           NOT_DELEGATED_TUNNEL_R15
	100.18.18.18    100.16.16.16    up      delegated              11  disabled    20h44m21s        DELEGATED_TUNNEL_R18
	100.18.18.18    100.16.16.16    up      not-configured                         20h44m21s        NOT_CONFIGURED_DELEGATED_TUNNEL_R18
	100.18.18.18    100.16.16.16    up      delegated               5  enabled     20h44m21s        DELEGATED_TUNNEL_R18_STICKY_ERO


**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 10.0    | Command introduced                                         |
+---------+------------------------------------------------------------+
| 11.5.6  | Added uptime/downtime column for show brief view           |
+---------+------------------------------------------------------------+
| 16.1    | Command modified to display breif info of delegation state |
+---------+------------------------------------------------------------+


