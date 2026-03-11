system login session-timeout
----------------------------

**Minimum user role:** operator

CLI sessions are terminated when no activity is done for a predefined amount of time. If you start a prolonged action in the CLI foreground, the idle timer stops, and will restart when the foreground process ends and control is returned to the shell prompt.

The actions that cause the idle timer to stop are:

- All transaction commands (e.g. commit, rollback)

- Load

- Save

- All request commands

- All run commands, except run shell, for which a fixed timeout is set to 15 minutes.

To configure the maximum allowed idle-time before the CLI session is disconnected:

**Command syntax: session-timeout [interval]**

**Command mode:** config

**Hierarchies**

- system login

.. **Note**

	- no command sets the values to default

	- interval=0 means no timeout (inifinite session)

	- if user start another program to run in the foreground of the CLI, the idle timer control is stopped from being computed. The calculation of idle time of the CLI session is restarted only after the foreground process exits and the control is returned to the shell prompt.

	Relevant commands are:

	- All transactions commands (commit, rollback)

	- Load

	- Save

	- All request commands

	- All run commands except "run shell"

	- For run shell commands, timeout is fixed for 15 minutes for idle session

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                | Range | Default |
+===========+============================================================================================================================+=======+=========+
| interval  | The amount of time (in minutes) allowed for a CLI session to be idle (no keyboard input) before disconnecting the session. | 0..90 | 30      |
|           | An interval with value 0 means no timeout. The session will continue indefinitely.                                         |       |         |
+-----------+----------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# session-timeout 30
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no session-timeout

.. **Help line:** configure maximum time allowed for CLI session to be idle before it is disconnected. Idle is a session with no input from user via keyboard.

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 6.0     | Command introduced                      |
+---------+-----------------------------------------+
| 10.0    | Range changed from minimum 15 min to 0. |
+---------+-----------------------------------------+


