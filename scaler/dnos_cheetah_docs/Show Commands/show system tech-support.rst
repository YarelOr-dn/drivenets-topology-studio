show system tech-support
------------------------

**Minimum user role:** viewer

This command allows you to view the generated tech-support file.



**Command syntax: show system tech-support** password

**Command mode:** operational



.. **Internal Note**

	- password - show system configuration with passwords. By default, passwords are removed from the output

	- Link to complete list can be found here:

	- https://drivenets.atlassian.net/wiki/spaces/DV/pages/272695301/Tech-support+file

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                          |
+===========+======================================================================================================+
| password  | Displays the system configuration with passwords. By default, passwords are removed from the output. |
+-----------+------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system tech-support
	# J2-WCUN8320006 config-start [14-Mar-2019 22:27:06]

	routing-policy
	  community-list CL_LU
	    rule 100 allow value 4200:10
	  !
	  community-list CL_U
	    rule 100 allow value 4200:20
	  !
	  policy 222_ROUTES
	    rule 10 allow
	      match ipv4 prefix LIMIT_222
	    !
	  !
	  policy BGP-LS-NH
	    rule 10 allow
	      description "Set NH for BGP-LS NLRI"
	      set local-preference 500
	      set community 500:500
	    !
	  !
	  policy BGP_X-LEAF_LU_OUT
	    rule 100 allowshow ndp [14-Mar-2019 22:26:14]:


	| IPv6 Address              | MAC Address       | State            | Interface     |
	|---------------------------+-------------------+------------------+---------------|
	| fe80::201:2ff:fe00:f9d    | 00:01:02:00:0f:9d | STALE            | ge100-0/0/39  |
	| 2001::3                   | 00:13:01:00:00:02 | REACHABLE        | bundle-1.402  |
	| fe80::201:2ff:fe00:f9c    | 00:01:02:00:0f:9c | REACHABLE        | bundle-30     |
	| 1414::2                   | e4:fc:82:e6:70:38 | ROUTER STALE     | bundle-20.450 |
	| fe80::201:2ff:fe00:fa1    | 00:01:02:00:0f:a1 | STALE            | bundle-40.10  |
	| fe80::e6fc:8201:c2e6:7038 | e4:fc:82:e6:70:38 | ROUTER REACHABLE | bundle-20.450 |
	| 2001::1                   | 00:13:01:00:00:01 | REACHABLE        | bundle-1.401  |
	| fe80::e6fc:82ff:fee6:7026 | e4:fc:82:e6:70:26 | ROUTER REACHABLE | bundle-10     |

	show services sla-probe summary [14-Mar-2019 22:26:15]:

	| Owner   | Test   | Target   | Total Probes   | Probe Type   | Probe Interval   | Test Interval   | History Size   | Source Address   |
	|---------+--------+----------+----------------+--------------+------------------+-----------------+----------------+------------------|

	show system aaa-servers tacacs [14-Mar-2019 22:26:15]:


	Admin state: disabled

	| Server Type   | IP Address   | Port   | Timeout   |
	|---------------+--------------+--------+-----------|


.. **Help line:** generate system tech-support file

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 11.0    | Completely new output |
+---------+-----------------------+
