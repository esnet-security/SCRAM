Feature: FlowSpec rules through the translator
  scenario added and then sweeps the FlowSpec RIB, so the path counts asserted below are absolute,
  and the clean_slate guards prove that cleanup is working.

  Scenario: A well formed IPv4 rule round trips through the wrapper
    When a flowspec rule is added
      | destination  | source        | protocol | source-port | destination-port | action  |
      | 10.40.0.0/16 | 192.0.2.40/32 | 6        | 22          | 80               | discard |
    Then exactly 1 IPv4 and 0 IPv6 flowspec paths are stored in the RIB
    Then the flowspec check finds the rule
    Then deleting the rule removes it cleanly
    Then no unicast routes are stored in the RIB

  Scenario: A rule with a port above 255 can never be found or deleted
    # broken
    When a flowspec rule is added
      | destination  | source        | protocol | source-port | destination-port | action  |
      | 10.42.0.0/16 | 192.0.2.42/32 | 6        |             | 443              | discard |
    Then exactly 1 IPv4 and 0 IPv6 flowspec paths are stored in the RIB
    Then the flowspec check does not find the rule
    Then deleting the rule warns and leaves it in the RIB

  Scenario: A pure IPv6 rule can never be found or deleted
    # broken?
    When a flowspec rule is added
      | destination     | source          | protocol | source-port | destination-port | action  |
      | 2001:db8:1::/64 | 2001:db8:2::/64 | 6        |             | 80               | discard |
    Then exactly 0 IPv4 and 1 IPv6 flowspec paths are stored in the RIB
    Then the flowspec check does not find the rule
    Then deleting the rule warns and leaves it in the RIB

  Scenario: A string protocol crashes the wrapper
    # might be broken
    When a flowspec rule is added but the wrapper raises
      | destination  | source        | protocol | source-port | destination-port | action  |
      | 10.41.0.0/16 | 192.0.2.41/32 | "6"      |             | 80               | discard |
    Then exactly 0 IPv4 and 0 IPv6 flowspec paths are stored in the RIB

  Scenario: A v4 flowspec message round trips through process()
    When a flowspec message is received
      | type                    | destination   | source        | protocol | source-port | destination-port | action  |
      | translator_filter_add   | 192.0.2.240/32 | 192.0.2.241/32 | 17       |             | 22               | discard |
    Then the translator sends no message back
    Then exactly 1 IPv4 and 0 IPv6 flowspec paths are stored in the RIB
    Then no unicast routes are stored in the RIB
    When a flowspec message is received
      | type                   | destination    | source        | protocol | source-port | destination-port | action  |
      | translator_filter_check | 192.0.2.240/32 | 192.0.2.241/32 | 17      |             | 22               | discard |
    Then the translator sends a check response reporting true is_blocked
    When a flowspec message is received
      | type                     | destination    | source        | protocol | source-port | destination-port | action  |
      | translator_filter_remove | 192.0.2.240/32 | 192.0.2.241/32 | 17      |             | 22               | discard |
    Then the translator sends no message back
    Then exactly 0 IPv4 and 0 IPv6 flowspec paths are stored in the RIB
    When a flowspec message is received
      | type                   | destination    | source        | protocol | source-port | destination-port | action  |
      | translator_filter_check | 192.0.2.240/32 | 192.0.2.241/32 | 17      |             | 22               | discard |
    Then the translator sends a check response reporting false is_blocked

  Scenario: The v6 flowspec message bug leaves an orphan the check reports as not blocked
    # also bugged
    When a flowspec message is received
      | type                  | destination     | source          | protocol | source-port | destination-port | action  |
      | translator_filter_add | 2001:db8:3::/64 | 2001:db8:4::/64 | 6        |             | 80               | discard |
    Then exactly 0 IPv4 and 1 IPv6 flowspec paths are stored in the RIB
    When a flowspec message is received
      | type                    | destination     | source          | protocol | source-port | destination-port | action  |
      | translator_filter_check | 2001:db8:3::/64 | 2001:db8:4::/64 | 6        |             | 80               | discard |
    Then the translator sends a check response reporting false is_blocked
    When a flowspec message is received
      | type                     | destination     | source          | protocol | source-port | destination-port | action  |
      | translator_filter_remove | 2001:db8:3::/64 | 2001:db8:4::/64 | 6        |             | 80               | discard |
    Then the translator logged Attempted to delete a FlowSpec path that is not in the RIB
    Then exactly 0 IPv4 and 1 IPv6 flowspec paths are stored in the RIB
