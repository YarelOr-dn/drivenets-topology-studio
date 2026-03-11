policy match extcommunity
-------------------------

**Minimum user role:** operator

To match BGP updates by extended community list:

**Command syntax: match extcommunity [extcommunity-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------------------+----------------------------------------------------+----------------------+-------------+
|                           |                                                    |                      |             |
| Parameter                 | Description                                        | Range                | Default     |
+===========================+====================================================+======================+=============+
|                           |                                                    |                      |             |
| extcommunity-list-name    |  The extended community-list's name to match.      | 1..255 characters    | \-          |
+---------------------------+----------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow

	dnRouter(cfg-rpl-policy-rule-10)# match extcommunity XCL_LP90


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match extcommunity


.. **Help line:** Match by extended community list

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+