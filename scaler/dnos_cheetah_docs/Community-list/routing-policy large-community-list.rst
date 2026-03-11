routing-policy large-community-list
-----------------------------------

**Minimum user role:** operator

BGP Large Communities are a way to signal information between networks.  Large BGP Communities are composed of a 12-byte path attribute constructed from a set of 3 uint32 values. An example of a Large Community is: 2914:65400:38016.
To define a new large community list and enter its configuration mode:

**Command syntax: large-community-list [large-community-list-name]**

**Command mode:** config

**Hierarchies**

- routing policy

**Note**

- Notice the change in prompt.

..  no commands remove the large-community-list configuration

..  validation:

**Parameter table**

+------------------------------+--------------------------------------------------+------------------+-------------+
|                              |                                                  |                  |             |
| Parameter                    | Description                                      | Range            | Default     |
+==============================+==================================================+==================+=============+
|                              |                                                  |                  |             |
| large-community-list-name    | The name of the large-community-list (string)    | length 1..255    | \-          |
+------------------------------+--------------------------------------------------+------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# large-community-list CL_NAME
	dnRouter(cfg-rpl-lcl)#

**Removing Configuration**

To delete a large community list:
::

	dnRouter(cfg-rpl)# no large-community-list CL_NAME

.. **Help line:** Configure large-community-list

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.1      | Command introduced    |
+-----------+-----------------------+
