routing-policy community-list rule
----------------------------------

**Minimum user role:** operator

To configure rules for standard community lists:

**Command syntax: rule [rule-id] [rule-type] {value [community] \| well-known [well-known-community] \| regex [regex] }**

**Command mode:** config

**Hierarchies**

- routing policy community list

**Note**

-  You can configure multiple communities in a single community list.

-  Communities from the 65535:<id> range are reserved as well known communities assigned by IANA.

-  You must set at least one community to configure community-list.

**Parameter table**

+-------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+---------+
|                         |                                                                                                                                                                                                                  |                                                                           | Default |
| Parameter               | Description                                                                                                                                                                                                      | Range                                                                     |         |
+=========================+==================================================================================================================================================================================================================+===========================================================================+=========+
|                         |                                                                                                                                                                                                                  |                                                                           | \-      |
| rule-id                 | The rule's unique identifier within the community list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule. | 1..65534                                                                  |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         | The default ID (65535) is assigned by the system to "Deny any" when no match is found.                                                                                                                           |                                                                           |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         | When configuring a rule ID that is already in use, all of the original rules' entries are overwritten.                                                                                                           |                                                                           |         |
+-------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+---------+
|                         |                                                                                                                                                                                                                  |                                                                           | \-      |
| rule-type               | Defines whether the traffic matching the rule conditions are to be   allowed or denied.                                                                                                                          | allow                                                                     |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | deny                                                                      |         |
+-------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+---------+
|                         |                                                                                                                                                                                                                  |                                                                           | \-      |
| community               | The community number (e.g.   aa:nn), range (e.g. aa-bb:nn)                                                                                                                                                       | AS_number: 0..65535                                                       |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         | <AS_number:id>,                                                                                                                                                                                                  | ID: 0..65535                                                              |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         | <lower_AS_number- upper_AS_number:lower_id-upper-id>                                                                                                                                                             |                                                                           |         |
+-------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+---------+
|                         |                                                                                                                                                                                                                  |                                                                           | \-      |
| well-known-community    | A reserved well-known community.                                                                                                                                                                                 | internet - advertise to all neighbors                                     |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | accept-own - first come first served                                      |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | Local-AS - cannot be advertised to eBGP neighbors                         |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | No-export - advertise only to same as neighbors                           |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | No-advertise - not advertised to any neighbor                             |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | No-LLGR - marks routes to not be treated according to LLGR rules          |         |
|                         |                                                                                                                                                                                                                  |                                                                           |         |
|                         |                                                                                                                                                                                                                  | LLGR-Stale - marks stale routes retained for a longer period of   time    |         |
+-------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+---------+
|                         |                                                                                                                                                                                                                  | \-                                                                        | \-      |
| regex                   | A regular expression defining a search pattern to match communities attribute in BGP updates.                                                                                                                    |                                                                           |         |
+-------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# community-list CL_NAME
	dnRouter(cfg-rpl-cl)# rule 10 allow value 65000:1000
	dnRouter(cfg-rpl-cl)# rule 20 allow value 8000-9000:2000
	dnRouter(cfg-rpl-cl)# rule 30 allow value 9500:2000-3000
	dnRouter(cfg-rpl-cl)# rule 40 allow value 10000-11000:40-50

	dnRouter(cfg-rpl-cl)# rule 50 allow well-known-community internet
	dnRouter(cfg-rpl-cl)# rule 60 allow well-known-community no-export

	dnRouter(cfg-rpl-cl)# rule 70 allow regex 65000:5000|_65000:3[0-9][0-9][0-9][0-9]

**Removing Configuration**

To remove a rule entry:
::

	dnRouter(cfg-rpl-cl)# no rule 20

.. **Help line:** add community to community list

**Command History**

+-------------+--------------------------------------------------------------+
|             |                                                              |
| Release     | Modification                                                 |
+=============+==============================================================+
|             |                                                              |
| 6.0         | Command introduced                                           |
+-------------+--------------------------------------------------------------+
|             |                                                              |
| 10.0        | Added well-known communities "no-llgr" and   "llgr-stale"    |
+-------------+--------------------------------------------------------------+
|             |                                                              |
| 11.5        | AS_number range changed from 1..65534 to 1..65535            |
+-------------+--------------------------------------------------------------+
