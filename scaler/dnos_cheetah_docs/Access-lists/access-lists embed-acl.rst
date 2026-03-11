access-lists embed-acl
----------------------

**Minimum user role:** operator


When you are required to create many rules that are common to many access-lists, the task of entering each rule individually to each access-list is extremely time-consuming. With the embedded functionality, you have the option to create an access-list with the common rules and apply those rules to a different access-lists and then use them in different interfaces across the system. By importing the embedded access-list, the rules of the embedded access-list will be added at a preference matching the embedded rule-id + offset.

The default rules of embedded access-list are not imported.

In-case of conflicting rules (where the rule-id of the imported embedded access-list overlaps a configured rule of the exclusive access-list), the exclusive access-list rules take precedence and will be installed in the datapath.

**Command syntax: embed-acl [access-list-name]** offset [offset]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule 

- access-lists ipv6 rule

**Note**

- The embedded access-list must match the type of the exclusive access-list (IPv4, IPv6). 

.. - Upon auto-complete, only matching type ACL will be shown. Commit validation is required

- Only one embedded access-list can be imported to an exclusive access-list.

- An embedded access-list that is imported to an exclusive access-list cannot have an embedded access-list called within it.

.. - required the following commit validation - the embedded-acl maximum configured rule-id + offset within the given exclusive ACL must be smaller than default rule-id. I.e: embedded-acl maximum configured rule-id + offset < 65534

- The embedded-acl maximum configured rule-id + the offset value within the exclusive ACL must be smaller than the default rule-id.


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------+-------------+-------------+
|                     |                                                                                           |             |             |
| Parameter           | Description                                                                               | Range       | Default     |
+=====================+===========================================================================================+=============+=============+
|                     |                                                                                           |             |             |
| access-list-name    | The configured ACL name.                                                                  | String      | \-          |
+---------------------+-------------------------------------------------------------------------------------------+-------------+-------------+
|                     |                                                                                           |             |             |
| offset              | Allows inserting an embedded ACL in the middle of   an already existing list of rules.    | 0..65434    | 0           |
+---------------------+-------------------------------------------------------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# embed-acl MY_EMBEDDED_IPV4_ACL
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# embed-acl MY_EMBEDDED_IPV6_ACL offset 100
	dnRouter(cfg-acl-ipv6)# exit


**Removing Configuration**

To remove the embedded access-list from the exclusive access-list configuration:
::

	dnRouter(cfg-acl-ipv4)# no embed-acl MY_EMBEDDED_IPV4_ACL

To revert the embedded access-list's offset to the default value:
::

	dnRouter(cfg-acl-ipv6)# no embed-acl MY_EMBEDDED_IPV6_ACL offset 100

.. **Help line:** Set an embedded ACL

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.1        | Command introduced    |
+-------------+-----------------------+
