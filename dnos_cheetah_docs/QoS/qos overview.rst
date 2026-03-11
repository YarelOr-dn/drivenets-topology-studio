Quality of Service (QoS) Overview
---------------------------------
A Quality of Service (QoS) policy is a set of rules used for managing network bandwidth, delay, jitter, and packet loss. A rule comprises a traffic-class to match and a list of actions to perform if the traffic-class condition is met. Within a QoS policy, rules are defined in order of execution. Each rule has an ID and the rules are executed in ascending order. A default rule is implicitly created for each policy, such that traffic that does not match any of the defined rules will match the default rule.

The QoS policy is attached to interfaces. See interfaces qos policy.

**Forwarding Classes and Queues**

Queue actions create queues for the forwarding class. There are five forwarding classes:

- Super Expedite Forwarding (super-ef)
- Expedite Forwarding (ef)
- High-Priority (hp)
- Assured Forwarding (af)
- Default Forwarding (df) - best effort

You can create a single queue per forwarding class, and up to 6 queues for the Assured Forwarding class (and altogether up to eight queues per policy).

The queue inherits its properties from the forwarding class to which it belongs. The queue properties are:

- Scheduling priority - strict priority according to traffic class level on the egress interfaces. While a higher forwarding class is still transmitting, all other forwarding classes are starved. If multiple af queues are created, the priority between them is according to a smart round-robin based on weight.

- Queue size - specifies the number of packets that a queue can hold for each forwarding class. Depending on the specified rules, packets satisfying the match criteria for a class accumulate in the queue reserved for the class until they are sent (according to strict priority). When the maximum packet threshold you defined for the class is reached, packets are dropped. The queue size is configured globally. See qos policy rule action queue size. In the event of buffer scarcity, the fair adaptive drop threshold (FADT) ensures that the buffer resources are shared fairly between the queues.

- Bandwidth - specifies the portion of the bandwidth that the queue is allowed to use. For priority queues (ef, hp, and sef), the max-bandwidth parameter is configured to prevent starvation of the lower priority queues. For af and df queues, the bandwidth parameter determines the ratio of the shared bandwidth that each queue can use. See qos policy rule action queue bandwidth.

Super-ef and ef queues can be configured with max-bandwidth to avoid starvation of lower priority queues. It is recommended to set a maximum bandwidth limit for these forwarding classes because otherwise they can use 100% of the port bandwidth.

You can limit the bandwidth on af queues to set their relative bandwidth in the forwarding-class. If you do not set a bandwidth limit, the queue will get an equal quota of the remaining bandwidth on the af forwarding-class in the policy. The remaining bandwidth is calculated as follows:

(100 - sum of bandwidth in af queues) / number of af queues

To calculate the total bandwidth for the af forwarding class:

aggregate rate (shape rate or physical rate) - sum of max-bandwidth configured on the higher priority forwarding-classes.

**Example**

Consider the following policy with 6 rules and a default rule:
::

	qos policy MyChildPolicy1_out

 rule 1

  match traffic-class myTrafficMap1

  actions

   queue super-ef max-bandwidth 10 percent

 rule 2

  match traffic-class myTrafficMap2

  actions

   queue ef max-bandwidth 15 percent

 rule 3

  match traffic-class myTrafficMap3

  actions

   queue hp max-bandwidth 25 percent

 rule 4

  match traffic-class myTrafficMap4

  actions

   queue af bandwidth 40 percent

 rule 5

  match traffic-class myTrafficMap5

  actions

   queue af bandwidth 20 percent

 rule 6

  match traffic-class myTrafficMap6

  actions

   queue af bandwidth 10 percent

 rule-default

  actions

   queue df bandwidth 5 percent

**Calculating the bandwidth for each af queue**

The sum of all bandwidth commands is 75 percent (40 + 20 + 10 +5).

The guaranteed bandwidth for all the af and df classes is 50% of the link bandwidth (100 - 20 (max-bandwidth of super-ef) - 15 (max bandwidth of ef ) - 25 (max bandwidth of hp ))

The guaranteed bandwidth of a specific af (or for df) is the relative rate for that class.

For example, the guaranteed bandwidth for af with bandwidth 40% on a 100Gbps link is 26.66 Gpbs ((40% / 75%) * 50% of 100Gpbs).

**Calculating the bandwidth for the af forwarding class**

The guaranteed bandwidth of the af forwarding class is calculated as follows:

100 - (20 + 30) = 50%

So if the physical rate of the interface is 100 Mbps (assuming no shaping), then the af forwarding class will be guaranteed 42.5 Mbps. This rate is divided to 4 queues, according to rules 3-6:

af queue 3 (rule 3) - is guaranteed 25% of 50 Mbps (i.e. 7.5 Mbps)

af queue 4 (rule 4) - is guaranteed 40% of 50 Mbps (i.e. 20 Mbps)

af queue 5 (rule 5) - is guaranteed 20% of 50 Mbps (i.e. 10 Mbps)

af queue 6 (rule 6) - is guaranteed 10% of 50 Mbps (i.e. 5 Mpbs)

**Egress QoS Mechanisms**

- Scheduler - implements strict priority according to traffic class level on the egress interfaces. The forwarding classes are:
  - Super Expedite Forwarding (super-ef)
  - Expedite Forwarding (ef)
  - High-Priority (hp)
  - Assured Forwarding (af)
  - Default Forwarding (df) - best effort

While a higher forwarding class is still transmitting, all other forwarding classes are starved.

For each forwarding class except "af", only one queue can be opened. For "af", up to four queues can be opened. If multiple queues are opened for "af", the priority is according to a smart round-robin based on weight.

You can control the size of each queue by configuring tail-drop thresholds. See qos policy rule action queue size.

- Shaper - excess traffic is delayed in a buffer so that traffic can be sent at a constant rate. A shaping action is typically configured on egress interfaces.