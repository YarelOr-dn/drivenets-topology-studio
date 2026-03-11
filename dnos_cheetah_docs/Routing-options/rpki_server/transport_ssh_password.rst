routing-options rpki server transport ssh password
--------------------------------------------------

**Minimum user role:** operator

To configure the password for the SSH transport session with the BGP RPKI cache-server.

**Command syntax: transport ssh password [ssh-session-password]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**

- If the authentication secret is not entered with the command, then the user will be prompted to enter a password.

**Parameter table**

+----------------------+---------------------------------------------------------------+------------------+---------+
| Parameter            | Description                                                   | Range            | Default |
+======================+===============================================================+==================+=========+
| ssh-session-password | Set a password for the SSH session with the RPKI cache-server | | string         | \-      |
|                      |                                                               | | length 1-255   |         |
+----------------------+---------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport ssh password EncryptedPassword

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# transport ssh password
    Enter password:
    Enter password for verification:


**Removing Configuration**

To remove the configured SSH password:
::

    dnRouter(cfg-routing-options-rpki)# no transport ssh password

To remove the configured transport configuration:
::

    dnRouter(cfg-routing-options-rpki)# no transport

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 15.1    | Command introduced                    |
+---------+---------------------------------------+
| 15.2    | Removed MD5 from the command's syntax |
+---------+---------------------------------------+
