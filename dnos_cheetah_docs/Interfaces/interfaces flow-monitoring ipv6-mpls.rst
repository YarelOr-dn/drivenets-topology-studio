interfaces flow-monitoring type ipv6-over-mpls template direction
-----------------------------------------------------------------

**Minimum user role:** operator

The interface flow-monitoring command defines a flow-monitoring profile for the interface. That is, it defines how flow-monitoring is applied on the interface: which flow-monitoring template to use, in which direction, which sampler profile to use, etc.

To define a flow-monitoring profile for the interface:

**Command syntax: flow-monitoring type ipv6-over-mpls template [template] direction [direction]** sampler-profile [sampler-profile]

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan

- You can attach up to 4 flow-monitoring templates per interface (one per type).

- If you do not set a flow-sampler, the sampling rate will be set to 1:1.

- If both ipv4-over-mpls and ipv6-over-mpls templates are attachd to the same interface, they must be attached with the same sampler-profile.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------------------------------------------------------+---------+
| Parameter       | Description                                                                      | Range                                                   | Default |
+=================+==================================================================================+=========================================================+=========+
| template        | The name of an existing flow-monitoring template. You can associate only one     | String (see "services flow-monitoring template")        | \-      |
|                 | flow-monitoring template per type. You can select only templates that match the  |                                                         |         |
|                 | selected type.                                                                   |                                                         |         |
+-----------------+----------------------------------------------------------------------------------+---------------------------------------------------------+---------+
| direction       | The direction in which the template applies                                      | in                                                      | in      |
+-----------------+----------------------------------------------------------------------------------+---------------------------------------------------------+---------+
| sampler-profile | The name of an existing flow-sampler.                                            | String (see "services flow-monitoring sampler-profile") | \-      |
+-----------------+----------------------------------------------------------------------------------+---------------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces ge100-1/1/1.100
    dnRouter(cfg-if-ge100-1/1/1.100)# flow-monitoring type ipv6-over-mpls template myTemplate direction in
    dnRouter(cfg-if-ge100-1/1/1.100)# flow-monitoring type ipv6-over-mpls template myTemplate direction in sampler-profile mySampler1


**Removing Configuration**

To remove the template attachment for all traffic types:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no flow-monitoring

To remove the template attachment for all traffic of IPv6 over MPLS:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no flow-monitoring type ipv6-over-mpls

To remove the sampler-profile:
::

    dnRouter(cfg-if-ge100-1/1/1.100)# no flow-monitoring type ipv6-over-mpls template myTemplate direction in sampler-profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
