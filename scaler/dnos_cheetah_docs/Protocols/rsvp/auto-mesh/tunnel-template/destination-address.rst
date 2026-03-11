protocols rsvp auto-mesh tunnel-template destination-address
------------------------------------------------------------

**Minimum user role:** operator

The tunnel-template destination-address differs from the regular tunnel destination-address command in that it takes a prefix-list rather than a single destination-address. The prefix-list indicates for which destinations the creation of auto-mesh tunnels is allowed. The prefix list is matched against the router-ids in the TE topology database. If a matching destination address is found in the database, a tunnel will be automatically created.

If the tunnel's destination address is unreachable, the tunnel will remain in a "down" state.

If the tunnel's destination address is not found in the database and the tunnel is in "down" state, the tunnel is deleted.

The template destination-address prefix-list is a mandatory configuration for the tunnel-template.If the prefix-list has a "deny" statement, this will prevent tunnel creation to that destination. If you update the prefix-list (e.g. change from "allow" to "deny", or remove a prefix from the list), the corresponding tunnels will be removed.

If you attach the same prefix-list to multiple auto-mesh templates, multiple different tunnels will be created to the same destination - one per template.

You can configure different auto-mesh templates that are configured with different prefix-lists that have overlapping prefixes.

To configure the destination-address (prefix-list) for the template:

**Command syntax: destination-address [destination-address-prefix-list]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template

**Note**
- It is not possible to remove the destination-address from the configuration. You can, however, run the command again with a different prefix-list-name, or you can remove the template and start over.

**Parameter table**

+---------------------------------+-------------------------+----------------+---------+
| Parameter                       | Description             | Range          | Default |
+=================================+=========================+================+=========+
| destination-address-prefix-list | rsvp tunnel destination | string         | \-      |
|                                 |                         | length 1..255  |         |
+---------------------------------+-------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# destination-address IPv4_PL_AutoMesh_1


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp-auto-mesh-temp)# no destination-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
