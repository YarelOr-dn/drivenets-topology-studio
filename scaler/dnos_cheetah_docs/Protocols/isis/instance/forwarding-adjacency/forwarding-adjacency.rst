protocols isis instance forwarding-adjacency
--------------------------------------------

**Minimum user role:** operator

Forwarding adjacency allows steering traffic into an existing RSVP-TE tunnel by using a primary tunnel as a forwarding adjacency in the IS-IS instance, allowing IS-IS traffic to be forwarded over the RSVP tunnel. The tunnel is added as a regular link to the IS-IS topology. The formed adjacency exists as long as the RSVP LSP is up.

To enter the forwarding-adjacency configuration hierarchy:

**Command syntax: forwarding-adjacency [tunnel-name]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- The RSVP tunnel must be an existing primary tunnel name.

- The tunnel must be configured in the same IS-IS instance.

- The same tunnel cannot be set as a forwarding-adjacency in multiple IS-IS instances.

- The tunnel cannot be enabled with shortcut, either explicitly or inherit.

**Parameter table**

+-------------+--------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                        | Range            | Default |
+=============+====================================================================+==================+=========+
| tunnel-name | The RSVP tunnel name over which forwarding-adjacency is configured | | string         | \-      |
|             |                                                                    | | length 1-255   |         |
+-------------+--------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# forwarding-adjacency TUNNEL_1
    dnRouter(cfg-isis-inst-fa)#


**Removing Configuration**

To remove the specific tunnel forwarding-adjacency configuration:
::

    dnRouter(cfg-protocols-isis-inst)# no forwarding-adjacency TUNNEL_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
