show cli history
----------------

**Minimum user role:** viewer

All valid commands entered by the user are logged if the user hit the Enter key. Up to 10,000 commands are logged per command mode. When the limit is reached, an older command is deleted to make room for a new command. You can show the commands that you have used throughout the session. You cannot view another user's CLI history.

If the session in non-configuration mode, the command will display the history of the operational commands since the beginning of the session.

If the session is in configuration mode, the command will display both the configuration and operational commands since the beginning of the session (i.e., since entering config-mode overall).

The history is maintained for each command mode separately, so that if you exit and re-enter a command mode, the logging continues from the point you left it.

Using the "up arrow" key will scroll the through the commands in the history for the command mode.

To display a list of the commands that you entered, use the following command:

**Command syntax: show cli history** [number-of-commands]

**Command mode:** operational



**Note**

- The commands displayed are for the current session. When you log out, the CLI history is cleared.

- User responses to CLI prompted questions are not logged.

..
	- All cli commands done by user are logged (each valid command followed by enter considered as command line)

	- Once user logs out, the history is cleared

	- A user cannot see other user CLI history commands

	- "number-of-commands" show the number of last cli commands. By default, all commands are shown.

	- up to 10k commands are logged, after that the output log wrap around.

	- For long output, paging is supported

	- user responses for questions are not logged

**Parameter table**

+--------------------+------------------------------------------------------------------------------------+-----------+
| Parameter          | Description                                                                        | Range     |
+====================+====================================================================================+===========+
| number-of-commands | Filters your commands to display the last number of commands that you have entered | 1..10,000 |
+--------------------+------------------------------------------------------------------------------------+-----------+

The following information is displayed for each command entry:

+-----------+----------------------------------------------------------+
| Parameter | Description                                              |
+===========+==========================================================+
| Time      | The time the command was executed (DD MMM YYYY hh:mm:ss) |
+-----------+----------------------------------------------------------+
| User      | The name of the user who entered the command             |
+-----------+----------------------------------------------------------+
| Command   | The command that was executed                            |
+-----------+----------------------------------------------------------+

**Example**
::

	dnRouter# show cli history
	
	| #   | Time                          | Command                                                     |
	|-----+-------------------------------+-------------------------------------------------------------|
	| 1   | 11-Jun-2017 10:02:05          | show system                                                 |
	| 2   | 11-Jun-2017 10:03:05          | show interfaces                                             |
	| 3   | 11-Jun-2017 10:04:05          | clear arp                                                   |
	| 4   | 11-Jun-2017 10:05:05          | show config | grep test                                     |
	| 5   | 11-Jun-2017 10:06:05          | show cli history                                            |
	
	
	dnRouter# show cli history 2
	
	| #   | Time                          | Command                                                     |
	|-----+-------------------------------+-------------------------------------------------------------|
	| 4   | 11-Jun-2017 10:05:05          | show config | grep test                                     |
	| 5   | 11-Jun-2017 10:06:05          | show cli history 2                                          |
	
	

.. **Help line:** show cli command history

**Command History**

+---------+----------------------------------------------------------------------------------------+
| Release | Modification                                                                           |
+=========+========================================================================================+
| 5.1.0   | Command introduced                                                                     |
+---------+----------------------------------------------------------------------------------------+
| 9.0     | Command removed                                                                        |
+---------+----------------------------------------------------------------------------------------+
| 11.0    | Command re-introduced with the optional filter for number of commands                  |
+---------+----------------------------------------------------------------------------------------+
| 13.3    | Separated the command history logging per command mode (operational and configuration) |
+---------+----------------------------------------------------------------------------------------+


