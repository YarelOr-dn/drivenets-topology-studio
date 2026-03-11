commit check
------------

**Minimum user role:** operator

The system performs the following checks on the candidate configuration:

-	Syntax check

-	System validation checks

-	Resources check (where available) - for data path configuration (QoS, Access-lists, etc.).

You will receive a warning, if another user has committed before you and there is a conflict and will be prompted to act:

-	check-and-merge: both the "merge" and "commit check" operations will be performed

-	merge-only: only "merge" will be performed without "commit check"

-	abort: no operation will be performed

To verify that the candidate configuration is syntactically correct without committing the changes:

**Command syntax: commit check**

**Command mode:** operational

..
	**Internal Note**

	The checks performed:

	- Syntax check

	- System validations, YANG validations, XPath check

	- Resources check (where available). i.e for data path configurations (QoS, ACL etc)

	- For the case multiple users have committed and there is a conflict, the user will get the following warning:

	- Warning: User <name> committed at <time>, your configuration is out of sync. What would you like to do (check-and-merge, merge-only, abort) [abort]? "

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interface ge100-1/1/1 mac-address 10:22:33:44:55:00
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit check
	Commit check passed successfully
	
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# no interface bundle-1
	dnRouter(cfg)# commit check
	Commit check failed on:
		interface bundle-1

.. **Help line:** Verify that the candidate configuration is syntactically correct, but do not commit the changes

**Command History**

+-------------+--------------------------------------------+
|             |                                            |
| Release     | Modification                               |
+=============+============================================+
|             |                                            |
| 6.0         | Command introduced                         |
+-------------+--------------------------------------------+
|             |                                            |
| 11.5        | Updated options for conflicting commits    |
+-------------+--------------------------------------------+