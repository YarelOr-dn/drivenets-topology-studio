# DNOS Routing-policy Configuration Reference

This document contains the complete DNOS CLI Routing-policy configuration syntax from the official DriveNets documentation.

---

## as-path-acl-list
```rst
routing-policy as-path-list
---------------------------

**Minimum user role:** operator

When a prefix announcement passes through an AS, that AS adds its AS number to the AS-path attribute. An AS can reject an announcement for a route that it originated, or reject an announcement that contains the local AS number in its AS-path. In this way, the AS-path helps prevent looping announcements.
You can define an access-list rule for an AS-path to use with BGP.
To create an access-list rule for the AS-path and enter its configuration mode:

**Command syntax: as-path-list [as-path-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- validation: if a user tries to remove an as-path  *-*  list while it is attached to any policy or protocol, the following error should be displayed:

 Error: unable to remove as-path-list <as-path-acl-name>. as-path-list is attached to policy <policy-name>

**Parameter table**

+-------------------+-------------------------------------+------------------+---------+
| Parameter         | Description                         | Range            | Default |
+===================+=====================================+==================+=========+
| as-path-list-name | Provide a name for the as-path list | | string         | \-      |
|                   |                                     | | length 1-255   |         |
+-------------------+-------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
    dnRouter(cfg-rpl-asp)#


**Removing Configuration**

To remove the as-path rule entry:
::

    dnRouter(cfg-rpl)# no as-path-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## rule-passes-through
```rst
routing-policy as-path-list rule
--------------------------------

**Minimum user role:** operator

This command matches the BGP AS path using regular expressions.

**Command syntax: rule [rule-id] [rule-type] passes-through [passes-through-as]**

**Command mode:** config

**Hierarchies**

- routing-policy as-path-list

**Note**

- If no match was found, the AS number will be denied.

- Rule 65535 is reserved as default rule of deny any as-number

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| Parameter         | Description                                                                      | Range                     | Default |
+===================+==================================================================================+===========================+=========+
| rule-id           | The rule's unique identifier within the as-path list. It determines the priority | 1-65534                   | \-      |
|                   | of the rule (rules with a low ID number have priority over rules with high ID    |                           |         |
|                   | numbers). You must configure at least one rule.                                  |                           |         |
+-------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| rule-type         | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow                   | \-      |
|                   | denied.                                                                          | | deny                    |         |
+-------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| passes-through-as | Verifies if the specified AS numbers match the BGP AS path. The value can be a   | 0..4294967295 x-y (range) | \-      |
|                   | specific AS number (e.g. 7677) or a range (e.g. 65000-65020).                    |                           |         |
+-------------------+----------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
    dnRouter(cfg-rpl-asp)# rule 10 allow passes-through 65060
    dnRouter(cfg-rpl-asp)# rule 20 allow passes-through 65000-65100


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-asp)# no rule 10

**Command History**

+---------+------------------------------------------------------------------------------------+
| Release | Modification                                                                       |
+=========+====================================================================================+
| 6.0     | Command introduced                                                                 |
+---------+------------------------------------------------------------------------------------+
| 11.0    | Updated rule-id range to max 65534 as rule 65535 is reserved for the default rule. |
+---------+------------------------------------------------------------------------------------+
```

## rule-regex
```rst
routing-policy as-path-list rule
--------------------------------

**Minimum user role:** operator

This command matches the BGP AS path using regular expressions.

**Command syntax: rule [rule-id] [rule-type] regex [regex]**

**Command mode:** config

**Hierarchies**

- routing-policy as-path-list

**Note**

- A lower rule-id results in higher priority

- If no match was found, the AS number will be denied.

- Rule 65535 is reserved as default rule of deny any as-number

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| rule-id   | The rule's unique identifier within the as-path list. It determines the priority | 1-65534   | \-      |
|           | of the rule (rules with a low ID number have priority over rules with high ID    |           |         |
|           | numbers). You must configure at least one rule.                                  |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+
| rule-type | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow   | \-      |
|           | denied.                                                                          | | deny    |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+
| regex     | A regular expression defining a search pattern to match communities attribute in | \-        | \-      |
|           | BGP updates.                                                                     |           |         |
|           | See Regular Expressions.                                                         |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# as-path-list ASP_LOCAL
    dnRouter(cfg-rpl-asp)# rule 10 allow regex _64[5-9][0-9][0-9]_

    dnRouter(cfg-rpl-asp)# rule 20 allow regex _6555[0-1]_


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-asp)# no rule 10

**Command History**

+---------+------------------------------------------------------------------------------------+
| Release | Modification                                                                       |
+=========+====================================================================================+
| 6.0     | Command introduced                                                                 |
+---------+------------------------------------------------------------------------------------+
| 11.0    | Updated rule-id range to max 65534 as rule 65535 is reserved for the default rule. |
+---------+------------------------------------------------------------------------------------+
```

## bgp-prefix-sid-map
```rst
routing-policy bgp-prefix-sid-map
---------------------------------

**Minimum user role:** operator

BGP prefix-sid map allows operator to create a mapping between labeled-unicast prefixes to desired Segment Routing prefix-sid.
When used, BGP will treat the matched prefix path as if prefix-sid attribute (RFC 8669) was present.
To create a BGP prefix-sid map:

**Command syntax: bgp-prefix-sid-map [bgp-prefix-sid-map]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Parameter table**

+--------------------+--------------------------------------------------+------------------+---------+
| Parameter          | Description                                      | Range            | Default |
+====================+==================================================+==================+=========+
| bgp-prefix-sid-map | Name of the BGP Prefix-SID mapping configuration | | string         | \-      |
|                    |                                                  | | length 1-255   |         |
+--------------------+--------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# bgp-prefix-sid-map BGP_MAP
    dnRouter(cfg-rpl-bgp-psid-map)#


**Removing Configuration**

To remove BGP prefix-sid map
::

    dnRouter(cfg-rpl)# no bgp-prefix-sid-map BGP_MAP

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## route
```rst
routing-policy bgp-prefix-sid-map route index
---------------------------------------------

**Minimum user role:** operator

Configure a route for segment-routing prefix-sid mapping. The SID index will be used to generate
a prefix-sid attribute, which according to it bgp will allocate a local labeled-unicast label per RFC8669.
The range can be used to allocate multiple labels starting from the base configured route and SID index.

**Command syntax: route [ip-prefix] index [sid-index]** range [range]

**Command mode:** config

**Hierarchies**

- routing-policy bgp-prefix-sid-map

**Note**

- Assigned index must be within the locally configured SRGB range

- bgp-prefix-sid-map cannot have overlapping prefixes due to range usage

- A SID index value cannot be used for different prefixes


**Parameter table**

+-----------+----------------------------------------+----------------+---------+
| Parameter | Description                            | Range          | Default |
+===========+========================================+================+=========+
| ip-prefix | IP prefix for the route                | | A.B.C.D/x    | \-      |
|           |                                        | | X:X::X:X/x   |         |
+-----------+----------------------------------------+----------------+---------+
| sid-index | SID index value for the prefix         | 0-1048575      | \-      |
+-----------+----------------------------------------+----------------+---------+
| range     | Optional range value for the SID index | 1-65535        | 1       |
+-----------+----------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# bgp-prefix-sid-map MY_SID_MAP
    dnRouter(cfg-rpl-bgp-psid-map)# route 192.168.1.0/32 index 100

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# bgp-prefix-sid-map MY_SID_MAP
    dnRouter(cfg-rpl-bgp-psid-map)# route 2001:db8::/32 index 200 range 10


**Removing Configuration**

To remove a route SID mapping:
::

    dnRouter(cfg-rpl-bgp-psid-map)# no route 192.168.1.0/24

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## community-list
```rst
routing-policy community-list
-----------------------------

**Minimum user role:** operator

A community list is a user defined communities attribute list that can be used for matching or manipulating the communities attribute in updates. There are two types of community lists:

- Standard community list - defines the communities attribute

- Extended community list - defines the communities attribute string with regular expression

The standard community list is compiled into binary format and is directly compared to the BGP communities attribute in BGP updates. Therefore, the comparison is faster than in the extended community list.

To define a new standard community list and enter its configuration mode:

**Command syntax: community-list [community-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- You cannot delete a community list that is attached to a policy.

**Parameter table**

+---------------------+--------------------------------+------------------+---------+
| Parameter           | Description                    | Range            | Default |
+=====================+================================+==================+=========+
| community-list-name | The name of the community-list | | string         | \-      |
|                     |                                | | length 1-255   |         |
+---------------------+--------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# community-list CL_NAME
    dnRouter(cfg-rpl-cl)#


**Removing Configuration**

To delete a community list:
::

    dnRouter(cfg-rpl)# no community-list CL_NAME

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## rule-regex
```rst
routing-policy community-list rule
----------------------------------

**Minimum user role:** operator

To configure regex rules for standard community lists:

**Command syntax: rule [rule-id] [rule-type] regex [regex]**

**Command mode:** config

**Hierarchies**

- routing-policy community-list

**Note**

- You can configure multiple communities in a single community list.

- Communities from the 65535:<id> range are reserved as well known communities assigned by IANA.

- You must set at least one community to configure community-list.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| rule-id   | The rule's unique identifier within the community list. It determines the        | 1-65534   | \-      |
|           | priority of the rule (rules with a low ID number have priority over rules with   |           |         |
|           | high ID numbers). You must configure at least one rule.                          |           |         |
|           | The default ID (65535) is assigned by the system to 'Deny any' when no match is  |           |         |
|           | found.                                                                           |           |         |
|           | When configuring a rule ID that is already in use, all of the original rules'    |           |         |
|           | entries are overwritten.                                                         |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+
| rule-type | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow   | \-      |
|           | denied.                                                                          | | deny    |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+
| regex     | A regular expression defining a search pattern to match communities attribute in | \-        | \-      |
|           | BGP updates.                                                                     |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# community-list CL_NAME
    dnRouter(cfg-rpl-cl)# rule 10 allow regex 65000:5000|_65000:3[0-9][0-9][0-9][0-9]


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-cl)# no rule 10

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 6.0     | Command introduced                                      |
+---------+---------------------------------------------------------+
| 10.0    | Added well-known communities 'no-llgr' and 'llgr-stale' |
+---------+---------------------------------------------------------+
| 11.5    | AS_number range changed from 1..65534 to 1..65535       |
+---------+---------------------------------------------------------+
```

## rule-value
```rst
routing-policy community-list rule
----------------------------------

**Minimum user role:** operator

To configure 'value' rules for standard community lists:

**Command syntax: rule [rule-id] [rule-type] value [community-value]**

**Command mode:** config

**Hierarchies**

- routing-policy community-list

**Note**

- You can configure multiple communities in a single community list.

- Communities from the 65535:<id> range are reserved as well known communities assigned by IANA.

- You must set at least one community to configure community-list.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------------------------+---------+
| Parameter       | Description                                                                      | Range                   | Default |
+=================+==================================================================================+=========================+=========+
| rule-id         | The rule's unique identifier within the community list. It determines the        | 1-65534                 | \-      |
|                 | priority of the rule (rules with a low ID number have priority over rules with   |                         |         |
|                 | high ID numbers). You must configure at least one rule.                          |                         |         |
|                 | The default ID (65535) is assigned by the system to 'Deny any' when no match is  |                         |         |
|                 | found.                                                                           |                         |         |
|                 | When configuring a rule ID that is already in use, all of the original rules'    |                         |         |
|                 | entries are overwritten.                                                         |                         |         |
+-----------------+----------------------------------------------------------------------------------+-------------------------+---------+
| rule-type       | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow                 | \-      |
|                 | denied.                                                                          | | deny                  |         |
+-----------------+----------------------------------------------------------------------------------+-------------------------+---------+
| community-value | The community number (e.g. aa:nn), range (e.g. aa-bb:nn)                         | | AS_number: 0..65535   | \-      |
|                 | <AS_number:id>,                                                                  | | ID: 0..65535          |         |
|                 | <lower_AS_number-upper_AS_number:lower_id-upper_id>                              |                         |         |
+-----------------+----------------------------------------------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# community-list CL_NAME
    dnRouter(cfg-rpl-cl)# rule 10 allow value 65000:1000
    dnRouter(cfg-rpl-cl)# rule 20 allow value 8000-9000:2000
    dnRouter(cfg-rpl-cl)# rule 30 allow value 9500:2000-3000
    dnRouter(cfg-rpl-cl)# rule 40 allow value 10000-11000:40-50


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-lcl)# no rule 10

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 6.0     | Command introduced                                      |
+---------+---------------------------------------------------------+
| 10.0    | Added well-known communities 'no-llgr' and 'llgr-stale' |
+---------+---------------------------------------------------------+
| 11.5    | AS_number range changed from 1..65534 to 1..65535       |
+---------+---------------------------------------------------------+
```

## rule-well-known-community
```rst
routing-policy community-list rule
----------------------------------

**Minimum user role:** operator

To configure rules for reserved well-known standard community lists:

**Command syntax: rule [rule-id] [rule-type] well-known-community [well-known-community]**

**Command mode:** config

**Hierarchies**

- routing-policy community-list

**Note**

- You can configure multiple communities in a single community list.

- Communities from the 65535:<id> range are reserved as well known communities assigned by IANA.

- You must set at least one community to configure community-list.

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+--------------------------------------------------------------------------+---------+
| Parameter            | Description                                                                      | Range                                                                    | Default |
+======================+==================================================================================+==========================================================================+=========+
| rule-id              | The rule's unique identifier within the community list. It determines the        | 1-65534                                                                  | \-      |
|                      | priority of the rule (rules with a low ID number have priority over rules with   |                                                                          |         |
|                      | high ID numbers). You must configure at least one rule.                          |                                                                          |         |
|                      | The default ID (65535) is assigned by the system to 'Deny any' when no match is  |                                                                          |         |
|                      | found.                                                                           |                                                                          |         |
|                      | When configuring a rule ID that is already in use, all of the original rules'    |                                                                          |         |
|                      | entries are overwritten.                                                         |                                                                          |         |
+----------------------+----------------------------------------------------------------------------------+--------------------------------------------------------------------------+---------+
| rule-type            | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow                                                                  | \-      |
|                      | denied.                                                                          | | deny                                                                   |         |
+----------------------+----------------------------------------------------------------------------------+--------------------------------------------------------------------------+---------+
| well-known-community | A reserved well-known community.                                                 | | internet - advertise to all neighbors                                  | \-      |
|                      |                                                                                  | | accept-own - first come first served                                   |         |
|                      |                                                                                  | | Local-AS - cannot be advertised to eBGP neighbors                      |         |
|                      |                                                                                  | | No-export - advertise only to same as neighbors                        |         |
|                      |                                                                                  | | No-advertise - not advertised to any neighbor                          |         |
|                      |                                                                                  | | No-LLGR - marks routes to not be treated according to LLGR rules       |         |
|                      |                                                                                  | | LLGR-Stale - marks stale routes retained for a longer period of time   |         |
+----------------------+----------------------------------------------------------------------------------+--------------------------------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# community-list CL_NAME
    dnRouter(cfg-rpl-cl)# rule 10 allow well-known-community internet
    dnRouter(cfg-rpl-cl)# rule 20 allow well-known-community no-export


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-cl)# no rule 10

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 6.0     | Command introduced                                      |
+---------+---------------------------------------------------------+
| 10.0    | Added well-known communities 'no-llgr' and 'llgr-stale' |
+---------+---------------------------------------------------------+
| 11.5    | AS_number range changed from 1..65534 to 1..65535       |
+---------+---------------------------------------------------------+
```

## extcommunity-list
```rst
routing-policy extcommunity-list
--------------------------------

**Minimum user role:** operator

A community list is a user defined communities attribute list that can be used for matching or manipulating the communities attribute in updates. There are two types of community lists:

- Standard community list - defines the communities attribute

- Extended community list - defines the communities attribute string with regular expression

The standard community list is compiled into binary format and is directly compared to the BGP communities attribute in BGP updates. Therefore, the comparison is faster than in the extended community list.

You can set multiple extcoummunities in a single extcommunity-list.

To define a new extended community list:

**Command syntax: extcommunity-list [extcommunity-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- You cannot delete an extcommunity list that is attached to a policy.

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter              | Description                                                                      | Range            | Default |
+========================+==================================================================================+==================+=========+
| extcommunity-list-name | The name of the extended community-list. The name cannot contain only numbers;   | | string         | \-      |
|                        | it must contain at least one letter.                                             | | length 1-255   |         |
+------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# extcommunity-list EXTCL_NAME
    dnRouter(cfg-rpl-extcl)#


**Removing Configuration**

To delete an extended community list:
::

    dnRouter(cfg-rpl)# no extcommunity-list EXTCL_NAME

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## rule color value
```rst
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
```

## rule regex
```rst
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
```

## rule-value
```rst
routing-policy extcommunity-list rule
-------------------------------------

**Minimum user role:** operator

To configure 'value' rules for extended community lists:

**Command syntax: rule [rule-id] [rule-type] [extcommunity-format] value [extcommunity-value]**

**Command mode:** config

**Hierarchies**

- routing-policy extcommunity-list

**Note**

- You can configure multiple communities in a single community list.

- Communities from the 65535:<id> range are reserved as well known communities assigned by IANA.

- Can be set a simple extcommunity value or an extcommunity range.

- Using [as-number-short]l or [as-number-short]L will code as-number-short number in a 32 bit field resulting in a Type1 route-distinguisher.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+---------------------------------------+---------+
| Parameter           | Description                                                                      | Range                                 | Default |
+=====================+==================================================================================+=======================================+=========+
| rule-id             | The rule's unique identifier within the community list. It determines the        | 1-65534                               | \-      |
|                     | priority of the rule (rules with a low ID number have priority over rules with   |                                       |         |
|                     | high ID numbers). You must configure at least one rule.                          |                                       |         |
|                     | The default ID (65535) is assigned by the system to 'Deny any' when no match is  |                                       |         |
|                     | found.                                                                           |                                       |         |
|                     | When configuring a rule ID that is already in use, all of the original rules'    |                                       |         |
|                     | entries are overwritten.                                                         |                                       |         |
+---------------------+----------------------------------------------------------------------------------+---------------------------------------+---------+
| rule-type           | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow                               | \-      |
|                     | denied.                                                                          | | deny                                |         |
+---------------------+----------------------------------------------------------------------------------+---------------------------------------+---------+
| extcommunity-format | [rt]: A route target is a BGP extended communities attribute that defines which  | | rt                                  | \-      |
|                     | VPN routes are exported and imported on the routers.                             | | soo                                 |         |
|                     | [soo]: BGP site of origin (SoO) is a tag that is appended on BGP updates to      |                                       |         |
|                     | allow to mark a specific peer as belonging to a particular site. By tagging the  |                                       |         |
|                     | route, BGP will check if the peer's site of origin is listed in the community    |                                       |         |
|                     | field. If it is then the route will be filtered. If not, then the route will be  |                                       |         |
|                     | advertised as normal.                                                            |                                       |         |
+---------------------+----------------------------------------------------------------------------------+---------------------------------------+---------+
| extcommunity-value  | Type0:                                                                           | | as-number-short: 0-65535            | \-      |
|                     | <[as-number-short]:[id-long]>                                                    | | as-number-long: (2^16)-4294967295   |         |
|                     | Type1:                                                                           | | id-short: 0-65535                   |         |
|                     | <[as-number-short]l:[id-short]>                                                  | | id-long: 0-4294967295               |         |
|                     | <[as-number-short]L:[id-short]>                                                  | | ipv4-address-prefix: A.B.C.D        |         |
|                     | <[as-number-long]:[id-short]>                                                    |                                       |         |
|                     | Type2:                                                                           |                                       |         |
|                     | <[ipv4-address-prefix]:[id-short]>                                               |                                       |         |
+---------------------+----------------------------------------------------------------------------------+---------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# extcommunity-list EXTCL_NAME
    dnRouter(cfg-rpl-extcl)# rule 10 allow rt value 65000:1000
    dnRouter(cfg-rpl-extcl)# rule 20 allow soo value 65000:2000
    dnRouter(cfg-rpl-extcl)# rule 30 deny rt value 65000l:5000
    dnRouter(cfg-rpl-extcl)# rule 40 deny soo value 9000L:500
    dnRouter(cfg-rpl-extcl)# rule 50 deny soo value 10.170.0.64:500

    dnRouter(cfg-rpl-extcl)# rule 110 allow rt value 4000-5000:1000
    dnRouter(cfg-rpl-extcl)# rule 120 allow soo value 50000-90000L:2000-3000
    dnRouter(cfg-rpl-extcl)# rule 130 deny rt value 10.180.2.64/24:10-50


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-lcl)# no rule 10

**Command History**

+---------+-------------------------+
| Release | Modification            |
+=========+=========================+
| 6.0     | Command introduced      |
+---------+-------------------------+
| 17.0    | Remove the regex option |
+---------+-------------------------+
```

## flowspec-local-policies
```rst
routing-policy flowspec-local-policies
--------------------------------------

**Minimum user role:** operator

To configure a policy based routing rule:

**Command syntax: flowspec-local-policies**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- Legal string length is 1-255 characters.

- Illegal characters include any whitespace and the following special characters (separated by commas): #,!,',”,\

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)#


**Removing Configuration**

To remove the specified flowspec-local-policies rule:
::

    dnRouter(cfg-rpl)# no flowspec-local-policies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
```

## large-community-list
```rst
routing-policy large-community-list
-----------------------------------

**Minimum user role:** operator

BGP Large Communities are a way to signal information between networks. Large BGP Communities are composed of a 12-byte path attribute constructed from a set of 3 uint32 values. An example of a Large Community is: 2914:65400:38016.
To define a new large community list and enter its configuration mode:

**Command syntax: large-community-list [large-community-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- Notice the change in prompt.

**Parameter table**

+---------------------------+--------------------------------------+------------------+---------+
| Parameter                 | Description                          | Range            | Default |
+===========================+======================================+==================+=========+
| large-community-list-name | The name of the large-community-list | | string         | \-      |
|                           |                                      | | length 1-255   |         |
+---------------------------+--------------------------------------+------------------+---------+

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

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## rule-regex
```rst
routing-policy large-community-list rule
----------------------------------------

**Minimum user role:** operator

To configure regex rules for large-community lists:

**Command syntax: rule [rule-id] [rule-type] regex [regex]**

**Command mode:** config

**Hierarchies**

- routing-policy large-community-list

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| rule-id   | The rule's unique identifier within the community list. It determines the        | 1-65534   | \-      |
|           | priority of the rule (rules with a low ID number have priority over rules with   |           |         |
|           | high ID numbers). You must configure at least one rule.                          |           |         |
|           | The default ID (65535) is assigned by the system to 'Deny any' when no match is  |           |         |
|           | found.                                                                           |           |         |
|           | When configuring a rule ID that is already in use, all of the original rules'    |           |         |
|           | entries are overwritten.                                                         |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+
| rule-type | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow   | \-      |
|           | denied.                                                                          | | deny    |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+
| regex     | A regular expression defining a search pattern to match large communities        | \-        | \-      |
|           | attribute in BGP updates.                                                        |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# large-community-list CL_NAME
    dnRouter(cfg-rpl-lcl)# rule 10 allow regex 65000:*:5000


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-lcl)# no rule 10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## rule-value
```rst
routing-policy large-community-list rule
----------------------------------------

**Minimum user role:** operator

To configure 'value' rules for large-community lists:

**Command syntax: rule [rule-id] [rule-type] value [large-community-value]**

**Command mode:** config

**Hierarchies**

- routing-policy large-community-list

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+----------------------------------------------+----------+
| Parameter             | Description                                                                      | Range                                        | Default  |
+=======================+==================================================================================+==============================================+==========+
| rule-id               | The rule's unique identifier within the community list. It determines the        | 1-65534                                      | \-       |
|                       | priority of the rule (rules with a low ID number have priority over rules with   |                                              |          |
|                       | high ID numbers). You must configure at least one rule.                          |                                              |          |
|                       | The default ID (65535) is assigned by the system to 'Deny any' when no match is  |                                              |          |
|                       | found.                                                                           |                                              |          |
|                       | When configuring a rule ID that is already in use, all of the original rules'    |                                              |          |
|                       | entries are overwritten.                                                         |                                              |          |
+-----------------------+----------------------------------------------------------------------------------+----------------------------------------------+----------+
| rule-type             | Defines whether the traffic matching the rule conditions are to be allowed or    | | allow                                      | \-       |
|                       | denied.                                                                          | | deny                                       |          |
+-----------------------+----------------------------------------------------------------------------------+----------------------------------------------+----------+
| large-community-value | <AS_number:id-1:id-2>                                                            | [0-4294967295]:[0-4294967295]:[0-4294967295] | \-:\-:\- |
+-----------------------+----------------------------------------------------------------------------------+----------------------------------------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# large-community-list CL_NAME
    dnRouter(cfg-rpl-lcl)# rule 10 allow value 15562:45:29


**Removing Configuration**

To remove a rule entry:
::

    dnRouter(cfg-rpl-lcl)# no rule 10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
```

## policy
```rst
routing-policy policy
---------------------

**Minimum user role:** operator

Policies provide a means to filter and/or apply actions to a route, thus allowing policies to be applied to routes. The policy includes an ordered list of entries, where each entry may specify the following:

- Matching conditions: the conditions which must be matched if the entry is to be considered further. If no conditions are defined, then the entry is always met. If more than one condition is defined, all conditions must be met.

- Set Actions: a policy entry may optionally specify one or more actions to set or modify attributes of the route. If multiple actions are defined, all actions are performed (if the proper conditions are met).

To create a policy and enter its configuration mode:

**Command syntax: policy [policy-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- You cannot delete a policy that is attached to a BGP or OSPF process.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| policy-name | Provide a name for the policy. Names with spaces must be enclosed in quotation   | | string         | \-      |
|             | marks. If you do not want to use quotation marks, do not use spaces.             | | length 1-255   |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)#

    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy ANOTHER_POLICY
    dnRouter(cfg-rpl-policy)#


**Removing Configuration**

To remove the policy:
::

    dnRouter(cfg-rpl-policy)# no policy MY_POLICY
    dnRouter(cfg-rpl-policy)# no policy ANOTHER_POLICY

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

## description
```rst
routing-policy prefix-list ipv4 description
-------------------------------------------

**Minimum user role:** operator

To add a description for the rule:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv4

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| description | Enter a description for the rule.                                                | | string         | \-      |
|             | Enter free-text description with spaces in between quotation marks. If you do    | | length 1-255   |         |
|             | not use quotation marks, do not use spaces.                                      |                  |         |
|             | For example:                                                                     |                  |         |
|             | ... description 'My long description'                                            |                  |         |
|             | ... description My_long_description                                              |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# prefix-list ipv4 prefix-list1
    dnRouter(cfg-rpl-pl)# description MyDescription_ForPrefixList1

    dnRouter(cfg-rpl)# prefix-list ipv4 prefix-list2
    dnRouter(cfg-rpl-pl)# description MyDescription_ForPrefixList2


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-rpl-pl)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+```

## prefix-list-ipv4
```rst
routing-policy prefix-list ipv4
-------------------------------

**Minimum user role:** operator

A community list is a user defined communities attribute list that can be used for matching or manipulating the communities attribute in updates. There are two types of community lists:
- Standard community list - defines the communities attribute
- Extended community list - defines the communities attribute string with regular expression
The standard community list is compiled into binary format and is directly compared to the BGP communities attribute in BGP updates. Therefore, the comparison is faster than in the extended community list.
To define a new standard community list and enter its configuration mode:

**Command syntax: prefix-list ipv4 [prefix-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- You cannot delete a prefix list that is attached to a policy.

**Parameter table**

+------------------+-----------------------------+------------------+---------+
| Parameter        | Description                 | Range            | Default |
+==================+=============================+==================+=========+
| prefix-list-name | The name of the prefix-list | | string         | \-      |
|                  |                             | | length 1-255   |         |
+------------------+-----------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# community-list CL_NAME
    dnRouter(cfg-rpl-cl)#


**Removing Configuration**

To delete a community list:
::

    dnRouter(cfg-rpl)# no community-list CL_NAME

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+```

## rule
```rst
routing-policy prefix-list ipv4 rules
-------------------------------------

**Minimum user role:** operator

To add a rule for the prefix list:

**Command syntax: rules [rules]** [, rules, rules]

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv4

**Parameter table**

+-----------+-------------------+-------+---------+
| Parameter | Description       | Range | Default |
+===========+===================+=======+=========+
| rules     | prefix list rules | \-    | \-      |
+-----------+-------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# prefix-list ipv4 prefix-list1
    dnRouter(cfg-rpl-pl)# rule 1 allow any
    dnRouter(cfg-rpl-pl)# rule 2 allow 1.2.3.4/32
    dnRouter(cfg-rpl-pl)# rule 3 deny 5.6.7.8/32


**Removing Configuration**

To remove the rule:
::

    dnRouter(cfg-rpl-pl)# no rule 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+```

## description
```rst
routing-policy prefix-list ipv6 description
-------------------------------------------

**Minimum user role:** operator

To add a description for the rule:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy prefix-list ipv6

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| description | Enter a description for the rule.                                                | | string         | \-      |
|             | Enter free-text description with spaces in between quotation marks. If you do    | | length 1-255   |         |
|             | not use quotation marks, do not use spaces.                                      |                  |         |
|             | For example:                                                                     |                  |         |
|             | ... description 'My long description'                                            |                  |         |
|             | ... description My_long_description                                              |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# prefix-list ipv4 prefix-list1
    dnRouter(cfg-rpl-pl)# description MyDescription_ForPrefixList1

    dnRouter(cfg-rpl)# prefix-list ipv4 prefix-list2
    dnRouter(cfg-rpl-pl)# description MyDescription_ForPrefixList2


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-rpl-pl)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+```

## prefix-list-ipv6
```rst
routing-policy prefix-list ipv6
-------------------------------

**Minimum user role:** operator

A community list is a user defined communities attribute list that can be used for matching or manipulating the communities attribute in updates. There are two types of community lists:
- Standard community list - defines the communities attribute
- Extended community list - defines the communities attribute string with regular expression
The standard community list is compiled into binary format and is directly compared to the BGP communities attribute in BGP updates. Therefore, the comparison is faster than in the extended community list.
To define a new standard community list and enter its configuration mode:

**Command syntax: prefix-list ipv6 [prefix-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Note**

- You cannot delete a prefix list that is attached to a policy.

**Parameter table**

+------------------+-----------------------------+------------------+---------+
| Parameter        | Description                 | Range            | Default |
+==================+=============================+==================+=========+
| prefix-list-name | The name of the prefix-list | | string         | \-      |
|                  |                             | | length 1-255   |         |
+------------------+-----------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# community-list CL_NAME
    dnRouter(cfg-rpl-cl)#


**Removing Configuration**

To delete a community list:
::

    dnRouter(cfg-rpl)# no community-list CL_NAME

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+```

## qppb-policy
```rst
routing-policy qppb-policy
--------------------------

**Minimum user role:** operator

A QoS qppb policy is a set of rules and is identified by a unique name.

To create a QoS qppb policy:

**Command syntax: qppb-policy [qppb-policy]**

**Command mode:** config

**Hierarchies**

- routing-policy

**Parameter table**

+-------------+------------------+------------------+---------+
| Parameter   | Description      | Range            | Default |
+=============+==================+==================+=========+
| qppb-policy | qppb policy name | | string         | \-      |
|             |                  | | length 1-255   |         |
+-------------+------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)#


**Removing Configuration**

To remove the qppb policy
::

    dnRouter(cfg-rpl)# no qppb-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
```

## routing-policy
```rst
routing-policy
--------------

**Minimum user role:** operator

You can create policies that are used by the various routing protocols.

The following types of policies are supported:

-	AS-path access-list
-	Community-list
-	extcommunity-list
-	large-community-list
-	Policy
-	Prefix-list

To enter routing policy configuration mode:

**Command syntax: routing-policy**

**Command mode:** config

**Note**

- You cannot remove a routing-policy that is being used.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)#


**Removing Configuration**

To remove all policies configuration (all as-path-lists, community-lists, extcommunity-lists, large-community-lists , policies and prefix-lists):
::

    dnRouter(cfg)# no routing-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
```

