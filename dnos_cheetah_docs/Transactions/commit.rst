commit
------

**Minimum user role:** operator

This command applies candidate configuration changes only. If no changes are made and commit is triggered, no action will be taken and an error message is displayed.
Use the no-warning with the commit command to discard warning output when another session has been committed before this commit action from the same running configuration. The system will merge the last commit.

A successful commit is timestamped with user indication.

Each successful commit generates a rollback-id.

If another user has committed before you and there is a conflict, you will receive a warning and will be prompted to act:

-	commit: both the "commit" and "merge" operations will be performed

-	merge-only: only "merge" will be performed without "commit"

-	abort: no operation will be performed

To apply the changed configuration:

**Command syntax: commit** no-warning

**Command mode:** operational

**Note**

- If you attempt to exit with uncommitted configurations, a warning is issued. Enter:

	- Yes - to commit and exit to root menu

	- No - to remove the candidate configuration ("rollback 0") and exit to root menu

	- Cancel - to remain in the config hierarchy with the candidate configuration as is (do not exit). This is the default option.


..
	**Internal Note**

	commit applies only a changed (candidate) configuration. in case configuration has not changed andcommitis triggered by the user, no action will be made to database & user will be prompt with "commit action is not applicable. no configuration changes were made".

	Successful commit (for each commit type) broadcasted to all logged-in users: "commit succeeded by $user at HH:MM:SS DD-MM-YYYY"

	Commit no-warning: Optional flag added to commit command. If the flag exists, system will discard warning output for the case in other session had been commit before the desired committed action from the same running configuration. System will merge last commit. flag valid also for commit checkcommand

	Each successful commit generates rollback-id, latest (current running configuration) has rollback-id 0. Overall 50 rollbacks supported with FIFO mechanism.

	If there are uncommitted configurations when user exits, CLI output will be: "Warning: Configuration includes uncommitted changes, would you like to commit them before exiting (yes,no,cancel)[cancel]?"

	"yes" - commit and exit to root menu

	"no" - remove the candidate config ("rollback 0") and exit to root menu

	"cancel" - remain in "cfg" menu with the candidate config as is.

	For the case multiple users have committed and there is a conflict, the user will get the following warning:

	Warning: User <name> committed at <time>, your configuration is out of sync. What would you like to do (commit, merge-only, abort) [abort]? "

	"commit" will perform the merge and commit operation

	"merge-only" will perform the merge without commit check operation

	"abort" will not perform any operation

	The default option is cancel


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interface ge100-1/1/1 mac-address 10:22:33:44:55:00
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit
	Commit succeeded by ADMIN at 27-Jan-2017 22:11:00 UTC
	
	dnRouter(cfg)# commit
	Commit action is not applicable. no configuration changes were made
	
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:02
	dnRouter(cfg)# no interface bundle-1
	dnRouter(cfg)# commit
	Commit check failed on:
		interface bundle-1

.. **Help line:** Commit the set of changes to the database and cause the changes to take operational effect

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+