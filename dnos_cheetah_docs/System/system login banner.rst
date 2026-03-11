system login banner 
--------------------

**Minimum user role:** operator

You can define a customized banner to be displayed before the username and password login prompts.

To define a login banner:

**Command syntax: banner [banner-message]**

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command removes the login banner

**Parameter table**

+----------------+--------------------------------------------------------------------------------+
| Parameter      | Description                                                                    |
+================+================================================================================+
| banner-message | Enter text that will appear before the login prompt. Start a new line with \n. |
+----------------+--------------------------------------------------------------------------------+

The banner is displayed when connecting to the NCP using:

- Console

- Telnet

- SSH

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# banner "This is My banner"
	dnRouter(cfg-system-login)# banner "This is My banner '@#$!<>"
	dnRouter(cfg-system-login)# banner "This is My \\ \" banner"

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no banner

.. **Help line:** Configure system login banner

**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 5.1.0   | Command introduced                                        |
+---------+-----------------------------------------------------------+
| 6.0     | Applied new hierarchy                                     |
+---------+-----------------------------------------------------------+
| 13.1    | Added banner display when connected via the console port. |
+---------+-----------------------------------------------------------+


