system aaa-server tacacs server priority address timeout
--------------------------------------------------------

**Minimum user role:** operator

Timeout determines the length of time that the NCR must wait for a connection to be established to a TACACS+server or for a response to be returned from the TACACS+ server. If the connection is terminated during a connection attempt, the current TACACS+ server will be marked as unavailable. The TACACS+request will be attempted on the next available TACACS+ server.

To define a timeout for the server:


**Command syntax: timeout [timeout]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- Notice the change in prompt

.. - no command reverts timeout to default value


**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| timeout   | The amount of time (in seconds) the device waits to receive a response from the  | 1..1000 | 5       |
|           | AAA server before it assumes that the server is unavailable.                     |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# timeout 60


**Removing Configuration**

To revert the timeout period to the default value:
::

    dnRouter(cfg-aaa-tacacs-server)# no timeout

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 5.1.0   | Command introduced                            |
+---------+-----------------------------------------------+
| 6.0     | Replaced "secret" with "password" in syntax   |
|         | Applied new hierarchy                         |
+---------+-----------------------------------------------+
| 10.0    | Applied new hierarchy                         |
+---------+-----------------------------------------------+
| 11.0    | Moved to "server" hierarchy                   |
+---------+-----------------------------------------------+
