routing-policy extcommunity-list rule
-------------------------------------

**Minimum user role:** operator

To set a match entry on a color extended community regular expression:

**Command syntax: rule [rule-id] [rule-type] regex [regex]**

**Command mode:** config

**Hierarchies**

- routing-policy extcommunity-list

**Note**

- Regex pattern is match on the Extended Community string as see on 'show bgp route'

- Can match on multiple extcommunity types with same pattern

- If specific extcommunity type is required pattern should include 'RT', 'SoO' or 'Color' to match type in string

- The option is mutually exclusive (per rule) with rt and soo extcommunity.

**Parameter table**

+-----------+------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                | Range     | Default |
+===========+============================================================+===========+=========+
| rule-id   | allow or deny the community                                | 1-65534   | \-      |
+-----------+------------------------------------------------------------+-----------+---------+
| rule-type | Action that will be done upon rule match (e.g. deny/allow) | | allow   | \-      |
|           |                                                            | | deny    |         |
+-----------+------------------------------------------------------------+-----------+---------+
| regex     | extcommunity regular expression                            | \-        | \-      |
+-----------+------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# extcommunity-list EXTCL_NAME
    dnRouter(cfg-rpl-extcl)# rule 10 allow color regex *
    dnRouter(cfg-rpl-extcl)# rule 10 allow regex 'RT:21{1,4}:100'
    dnRouter(cfg-rpl-extcl)# rule 10 allow regex 'SoO:40:100$'
    dnRouter(cfg-rpl-extcl)# rule 30 allow regex 'RT:21{1,4}:200|SoO:40:300$'
    dnRouter(cfg-rpl-extcl)# rule 10 allow regex 'Color:8000'


**Removing Configuration**

To delete the rule:
::

    dnRouter(cfg-rpl-extcl)# no rule 10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
