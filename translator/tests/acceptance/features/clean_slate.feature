Feature: Tests run correctly
  When running tests, there are no leftover blocks

  Scenario: No leftover v4 blocks
    Then 0.0.0.0/0 is unblocked

  Scenario: No leftover v6 blocks
    Then ::/0 is unblocked

  Scenario: No leftover v4 flowspec rules
    Then exactly 0 IPv4 flowspec paths are stored in the IPv4 RIB

  Scenario: No leftover v6 flowspec rules
    Then exactly 0 IPv6 flowspec paths are stored in the IPv6 RIB
