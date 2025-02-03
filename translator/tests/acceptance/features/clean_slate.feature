Feature: Tests run correctly
  When running tests, there are no leftover blocks

  Scenario: No leftover v4 blocks in base VRF
    Then 0.0.0.0/0 in base is unblocked

  Scenario: No leftover v6 blocks in base VRF
    Then ::/0 in base is unblocked

  Scenario: No leftover v4 blocks in test-vrf VRF
    Then 0.0.0.0/0 in test-vrf is unblocked

  Scenario: No leftover v6 blocks in test-vrf VRF
    Then ::/0 in test-vrf is unblocked
