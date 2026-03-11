system ssh
-----------

**Minimum user role:** operator

Secure shell (SSH) is a generic connection protocol used to provide remote access to a device and provide secured file transfer protocol. DNOS enables to configure an SSH Server to enable access to the NCR via SSH (CLI) and also multiple SSH Clients, to enable to access remote devices from the NCR via SSH.

SSH Server/Client must be available via in-band management (default VRF) or out-of-band (mgmt0 interface) only.

To manage SSH sessions:

**Command syntax: ssh [parameters]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt from dnRouter(cfg-system)# to dnRouter(cfg-system-ssh)# (system SSH configuration mode).

.. - no command returns the state to default.

**Parameter table**

+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| Parameter               | Description                                                                                                   | Reference                              |
+=========================+===============================================================================================================+========================================+
| client admin-state      | Enable or disable the client SSH functionality                                                                | system ssh client admin-state          |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server client-list      | Configure a list of incoming IP addresses that will or will not be permitted access to an in-band SSH server. | system ssh server vrf client-list      |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server client-list type | Sets the server client-list as a white-list or black-list.                                                    | system ssh server vrf client-list type |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server max-sessions     | Configure the maximum number of concurrent SSH sessions                                                       | system ssh server max-sessions         |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+
| server admin-state      | Enable/disable the SSH server                                                                                 | system ssh server admin-state          |
+-------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ssh
	dnRouter(cfg-system-ssh)# client admin-state enabled
	dnRouter(cfg-system-ssh)# server
	dnRouter(cfg-system-ssh-server)#



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ssh)# no client admin-state

.. **Help line:** configure ssh server and client functionality.

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 6.0     | Command introduced for new hierarchy |
+---------+--------------------------------------+
