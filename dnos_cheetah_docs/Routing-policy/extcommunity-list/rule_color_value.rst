routing-policy extcommunity-list rule
-------------------------------------

**Minimum user role:** operator

To set a match entry on a color extended community value:

**Command syntax: rule [rule-id] [rule-type] color value [color-value]**

**Command mode:** config

**Hierarchies**

- routing-policy extcommunity-list

**Note**

- option is mutually exclusive (per rule) with rt and soo extcommunity.

**Parameter table**

+-------------+------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                | Range        | Default |
+=============+============================================================+==============+=========+
| rule-id     | allow or deny the community                                | 1-65534      | \-      |
+-------------+------------------------------------------------------------+--------------+---------+
| rule-type   | Action that will be done upon rule match (e.g. deny/allow) | | allow      | \-      |
|             |                                                            | | deny       |         |
+-------------+------------------------------------------------------------+--------------+---------+
| color-value | extcommunity color value                                   | 0-4294967295 | \-      |
+-------------+------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# extcommunity-list EXTCL_NAME
    dnRouter(cfg-rpl-extcl)# rule 10 allow color value 10


**Removing Configuration**

To delete the rule:
::

    dnRouter(cfg-rpl-extcl)# no  rule 10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
