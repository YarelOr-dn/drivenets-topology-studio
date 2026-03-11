routing-options rpki server transport ssh username
--------------------------------------------------

**Minimum user role:** operator

To configure the username for the SSH transport session with the BGP RPKI cache-server.

**Command syntax: transport ssh username [ssh-username]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Parameter table**

+--------------+-------------------------------------------------+------------------+---------+
| Parameter    | Description                                     | Range            | Default |
+==============+=================================================+==================+=========+
| ssh-username | Username for SSH session with RPKI cache server | | string         | \-      |
|              |                                                 | | length 1-255   |         |
+--------------+-------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# transport ssh username RPKIValidator


**Removing Configuration**

To remove the configured SSH username:
::

    dnRouter(cfg-routing-options-rpki)# no transport ssh username

To remove the configured transport configuration:
::

    dnRouter(cfg-routing-options-rpki)# no transport

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
