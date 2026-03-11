system aaa-server tacacs server priority address port
-----------------------------------------------------

**Minimum user role:** operator

To configure the TCP port for the remote TACACS+ server:


**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- Notice the change in prompt.

.. - no command reverts to default value

    - Up to 5 TACACS servers are supported


**Parameter table**

+-----------+-----------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                 | Range     | Default |
+===========+=============================================================================+===========+=========+
| port      | The destination port number to use when sending requests to the AAA server. | 1..65,535 | 49      |
+-----------+-----------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# port 49


**Removing Configuration**

To revert the port number to the default value:
::

    dnRouter(cfg-aaa-tacacs-server)# no port

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
| 11.0    | Moved to "server" hierarchy"                  |
+---------+-----------------------------------------------+
