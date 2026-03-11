Accessing the CLI Terminal
--------------------------

**Minimum user role:** operator

The DNOS command line interface (CLI) is the primary interface you use to access, configure, and monitor the DriveNets Network Cloud Router. You can access the CLI from a remote location via SSH. DNOS supports up to 10 simultaneous SSH sessions. SSH sessions disconnect automatically after remaining idle for 30 minutes (configurable).

The CLI provides the following major features:

- Operation and configuration modes

- Command completion

- Context-sensitive help

To access the CLI, you need a valid user. Each user is assigned with a role that determines which operations the user can and cannot perform. See “system login user role”.

To access the CLI, log on to the NC system (NCE):

1. From a remote host, open an SSH session to the NCE.

2. At the prompt, enter the username for the server, press Enter.

3. At the prompt, enter the password for the server, press Enter. If login is successful, the server prompt of the main CLI terminal is displayed:

::

 dnRouter# 

4. Enter the necessary commands to complete your tasks.

To log off:

1. At the operation mode prompt, enter the exit command to exit the CLI.
::

 dnRouter# exit

Or enter the following command from any command mode to exit the CLI and close the CLI terminal:
::

 dnRouter(cfg-any-hierarchy)# quit

2. Press Enter.



