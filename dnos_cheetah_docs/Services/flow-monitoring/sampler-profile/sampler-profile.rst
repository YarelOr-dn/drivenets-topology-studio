services flow-monitoring sampler-profile
----------------------------------------

**Minimum user role:** operator

The sampler profile defines how to sample the traffic forwarded to the local CPU.

You can configure up to 8 sampler profiles per system. These profiles are attached to flow-monitoring interfaces (one sampler profile per interface). Thus, to collect IPv4 traffic and IPv6 traffic (using two different templates) different sampler profiles are defined for each type of traffic on a specific interface.

To create a sampler-profile:

**Command syntax: sampler-profile [sampler-profile]**

**Command mode:** config

**Hierarchies**

- services flow-monitoring

**Parameter table**

+-----------------+---------------------------------------------------------+-----------------+---------+
| Parameter       | Description                                             | Range           | Default |
+=================+=========================================================+=================+=========+
| sampler-profile | Reference to the configured name of the sampler-profile | | string        | \-      |
|                 |                                                         | | length 1-32   |         |
+-----------------+---------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# flow-monitoring
    dnRouter(cfg-srv-flow-monitoring)# sampler-profile mySampler


**Removing Configuration**

You cannot delete a sampler-profile if it is used by an interface. Remove the sampler profile from the interface configuration before deleting the profile.
To remove a specific sampler-profile:
::

    dnRouter(cfg-srv-flow-monitoring)# no sampler-profile mySampler

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
