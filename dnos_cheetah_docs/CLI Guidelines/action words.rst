Action Words
------------

The help description for menu items always begins with an action word (Configure, Display, Remove, etc.).

The help description for parameters never begins with an action word. It only describes the variable itself.

Example:

propagate-ttl Configure TTL propagation

<enabled> enable TTL propagation

<disabled> disable TTL propagation

The help for the menu item in Configuration mode is: Configure parameter. In the above example the parameter is TTL propagation, so the help for the corresponding menu item is Configure TTL propagation.

+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|          | Note that the help for the parameter is just the Parameter name. There is no need to add an action word: Enable or Disable TTL propagation. This is self-evident. |
+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The following are the main action words used:

Clear Clear operations

Configure Configure mode

load Load saved configuration

merge Merge configuration file

no Remove configuration

request Request operations

run Run a command

save Save current configuration

show Display information

Exceptions
~~~~~~~~~~

Sometimes, "configure" is not the correct action word for a menu item, even though the menu item is under the "configure" hierarchy.

Example

configure access-list ipv4 <acl_name> rule <rule_id> <<rule_type>> fragmented

configure Configure mode

access-list Configure access-list

ipv4 Configure IPv4 access-list type

<text> Access-list name (36 characters)

Rule Configure access-list rule

<1-65534> Rule identifier

<allow/deny> Rule type

Fragmented Match fragmented packets

For the menu item "fragmented", "Configure fragmented packets" would be incorrect. In this case, "Match fragmented packets" is accurate.
