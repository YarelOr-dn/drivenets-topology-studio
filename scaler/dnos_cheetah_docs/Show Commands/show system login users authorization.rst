show system login users authorization
-------------------------------------

**Minimum user role:** viewer

To view a specific user's access privileges:



**Command syntax: show system login users authorization [user-name]**

**Command mode:** operational



**Note**

- Authorization information is not available for local users.

- Authorization information for users logged in using TACACS display all received parameters from the TACACS including the assigned role

.. - For TACACS users, authorization can be presented only for current user.



**Example**
::

	dnRouter# show system login users authorization dnroot
	
	user: dnroot
	role: admin
	description:
	authorization: 
	cmd_deny = "show.arp" 
	cmd_deny = "show.arp.*" 
	cmd_deny = "show.system.*;show.config;show.config.system;show.config.control-terminal" 
	cmd_allow = " request.system.tech-support" 
	
	dnRouter# show system login users authorization MyUser
	
	authorization: 
	cmd_deny = "show.interfaces;show.interfaces.counters;show.arp;show.arp.interface;show.ndp;show.mpls; show.route; show.route.summary;show.system;show.system.hardware
	cmd_allow = show.system.uptime;show.acl;show.config;run.ping;run.traceroute; run.monitor;show.services;show.log;show.zebra"
	 
	dnRouter# show system login users authorization admin
	
	user: dnroot
	role: admin
	description:
	authorization: 
	
	


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


