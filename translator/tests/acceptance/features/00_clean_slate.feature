Feature: Tests run correctly
  When running tests, there are no leftover blocks

  Scenario: No leftover v4 blocks
    Then 0.0.0.0/0 is unblocked

  Scenario: No leftover v6 blocks
    Then ::/0 is unblocked
    aaaaaaaaaaaaaaaa