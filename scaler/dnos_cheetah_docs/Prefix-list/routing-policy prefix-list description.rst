routing-policy prefix-list description
--------------------------------------

**Minimum user role:** operator

To add a description for your prefix list:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv4|ipv6

**Parameter table:**

+----------------+------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+
|                |                                                                                                                                          |                       |
| Parameter      | Description                                                                                                                              | Range                 |
+================+==========================================================================================================================================+=======================+
|                |                                                                                                                                          |                       |
| description    | Enter a description for the   IP prefix-list.                                                                                            | 1..255 characters     |
|                |                                                                                                                                          |                       |
|                | Enter free-text description with spaces in between quotation   marks. If you do not use quotation marks, do not use spaces. For example: |                       |
|                |                                                                                                                                          |                       |
|                | ... description "My long description"                                                                                                    |                       |
|                |                                                                                                                                          |                       |
|                | ... description My_long_description                                                                                                      |                       |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+
| rule-type      | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                    | allow deny            |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+-----------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv4 PL_MARTIANS
	dnRouter(cfg-rpl-pl)# description MyDescription

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# prefix-list ipv6 PL6_MARTIANS
	dnRouter(cfg-rpl-pl6)# description MyDescription


**Removing Configuration**

To delete the description:
::

	dnRouter(cfg-rpl-pl6)# no description

.. **Help line:** Add description for an ip prefix-list

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+
