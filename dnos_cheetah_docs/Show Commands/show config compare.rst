show config compare
-------------------

**Minimum user role:** viewer

This command compares two configurations. When indicating a single rollback ID, the result is a comparison between the candidate configuration and the committed configuration indicated by the rollback ID. When indicating two rollback IDs, the result is a comparison between two committed configurations.

The command output displays additions in green and deletions in red.

For information about rollbacks, see rollback.

To compare configurations:

**Command syntax: show config compare** rollback [rollback-id-x] rollback [rollback-id-y]

**Command mode:** operational



**Note**

- Running show config compare (without rollback ID) compares the candidate to the running configuration. This is the same as running show config compare rollback 0.

..
	**Internal Note**

	- current committed - display changes of candidate vs the current applied configuration (show config compare)

	- rollback - display changes of candidate vs. apreviously committed configuration. (show config compare rollback [rollback-id])

	- Output supports add, delete, chage configuration changes.

**Parameter table**

+-------------+---------------------------------------------------------------------------+-------+---------+
| Parameter   | Description                                                               | Range | Default |
+=============+===========================================================================+=======+=========+
| rollback-id | The rollback-id of the commit transaction file to use for the comparison. | 0..49 | 0       |
+-------------+---------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces ge100-1/1/1 mac-address 10:22:33:44:55:00
	dnRouter(cfg)# interfaces bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# no interface bundle-2
	dnRouter(cfg)# commit
	commit succeeded by ADMIN at 27-Jun-2017 22:05:01
	
	dnRouter(cfg)# show config compare
	Added:
	interfaces ge100-1/1/1 
		+ mac-address 10:22:33:44:55:00
	+ interfaces ge100-1/1/2 mac-address 10:22:33:44:55:00
	Changed:
	- interfaces bundle-1 mac-address 00:00:00:00:00:55
	+ interfaces bundle-1 mac-address 00:00:00:00:00:01
	protocol bgp 1
	   neighbor 1.1.1.1
	    	- remote-as 50
	        + remote-as 60
	        - local-as 30
	        + local-as 20
	        - timer yes
	        + timer noe
	Deleted:
	- interfaces bundle-2
	
	dnRouter# show config compare rollback 1
	Added:
	interfaces ge100-1/1/1 
		+ mac-address 10:22:33:44:55:00
	+ interfaces ge100-1/1/2 mac-address 10:22:33:44:55:00
	Changed:
	- interfaces bundle-1 mac-address 00:00:00:00:00:55
	+ interfaces bundle-1 mac-address 00:00:00:00:00:01
	protocol bgp 1
	   neighbor 1.1.1.1
	    	- remote-as 50
	        + remote-as 60
	        - local-as 30
	        + local-as 20
	        - timer yes
	        + timer noe
	Deleted:
	- interfaces bundle-2

	dnRouter# show config compare rollback 5 rollback 10
	Added:
	interfaces ge100-1/1/1 
		+ mac-address 10:22:33:44:55:00
	+ interfaces ge100-1/1/2 mac-address 10:22:33:44:55:00
	Changed:
	- interfaces bundle-1 mac-address 00:00:00:00:00:55
	+ interfaces bundle-1 mac-address 00:00:00:00:00:01
	protocol bgp 1
	   neighbor 1.1.1.1
	    	- remote-as 50
	        + remote-as 60
	        - local-as 30
	        + local-as 20
	        - timer yes
	        + timer noe
	Deleted:
	- interfaces bundle-2
	

.. **Help line:** compares the candidate configuration with the current config / previously saved rollback configuration

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 6.0     | Command introduced                         |
+---------+--------------------------------------------+
| 11.4    | Added the ability to compare two rollbacks |
+---------+--------------------------------------------+
