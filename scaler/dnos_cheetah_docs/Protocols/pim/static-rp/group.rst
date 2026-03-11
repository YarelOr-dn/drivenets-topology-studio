protocols pim static-rp group
-----------------------------

**Minimum user role:** operator

Use the following command to configure the group ranges for a static RP.

**Command syntax: group [rp-group-prefix-list]**

**Command mode:** config

**Hierarchies**

- protocols pim static-rp

**Note**
- A static RP on which no prefix list is configured is mapped by default to the whole 224.0.0.0/4 range subtract the condigured SSM range. If ASM override is configured, the whole 224.0.0.0/4 range is assigned. 

- Only one static-rp is allowed with no-prefix-list.

- Assigning the same prefix list to two different static-RP addresses is not allowed.

- A static-rp can be assigned only with a single prefix-list. The second configured prefix-list will override the first.

- Two static-rps each defined with a different but overlapping prefix-list will be rejected.

**Parameter table**

+----------------------+--------------------------------------------------------------------------------+------------------+---------+
| Parameter            | Description                                                                    | Range            | Default |
+======================+================================================================================+==================+=========+
| rp-group-prefix-list | The prefix-list name which defines the group address ranges handled by the RP. | | string         | \-      |
|                      |                                                                                | | length 1-255   |         |
+----------------------+--------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# static-rp 2.2.2.2
    dnRouter(cfg-protocols-pim-rp)# group RP-2222-GROUP-MAPPING
    dnRouter(cfg-protocols-pim-rp)#


**Removing Configuration**

To remove the RP address group mapping thereby mapping the static RP address to the default non-SSM 224.0.0.0/4 group range:
::

    dnRouter(cfg-protocols-pim-rp)# no group RP-2222-GROUP-MAPPING

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
