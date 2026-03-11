policy match large-community
----------------------------

**Minimum user role:** operator

To match BGP updates by large-community using a large-community-list:

**Command syntax: match large-community [large-community-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+------------------------------+-----------------------------------------------+----------------------+-------------+
|                              |                                               |                      |             |
| Parameter                    | Description                                   | Range                | Default     |
+==============================+===============================================+======================+=============+
|                              |                                               |                      |             |
| large-community-list-name    |  The large-community-list-name to match.      | 1..255 characters    | \-          |
+------------------------------+-----------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow

	dnRouter(cfg-rpl-policy-rule-10)#  match large-community LARGE_CL_1


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)#  no match large-community


.. **Help line:** Match by large-community list

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 6.0         | Command introduced                      |
+-------------+-----------------------------------------+
|             |                                         |
| 10.0        | Match is done using a community-list    |
+-------------+-----------------------------------------+
|             |                                         |
| 11.0        | Removed the option for exact-match      |
+-------------+-----------------------------------------+