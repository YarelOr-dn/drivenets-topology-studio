system aaa-server tacacs authorization-type
-------------------------------------------

**Minimum user role:** operator

To configure the authorization type using the TACACS server:


**Command syntax: authorization-type [authorization-type]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs

**Note**

- If the TACACS server is unreachable, the timeout logic will be applied.

- If a 'command' type is used, every cli command will be sent to be authorized by the server.

- If a 'command' type is used, every cli command will be sent to be authorized by the server.

- If a 'session' type is used, the authorization requests will be done according to the authorization as was received from the server.

- If a 'session-and-command' type is used, the session authorization will be applied first, then the command authorization will be performed for every cli command executed by the user.

- TACACS message arguments are limited to 255 characters per argument.

**Parameter table**

+--------------------+------------------------------------------------+-------------------------+---------+
| Parameter          | Description                                    | Range                   | Default |
+====================+================================================+=========================+=========+
| authorization-type |  the authorization-type for all tacacs servers | | session               | session |
|                    |                                                | | command               |         |
|                    |                                                | | session-and-command   |         |
+--------------------+------------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# authorization-type command
    dnRouter(cfg-system-aaa-tacacs)#


**Removing Configuration**

To revert the authorization-type to default:
::

    dnRouter(system-aaa-tacacs)# no authorization-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
