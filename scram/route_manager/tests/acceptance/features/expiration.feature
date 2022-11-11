Feature: entries auto-expire
  Entries get semi-auto-expired

  Scenario: Adding an IP expires after calling process-expiration
    When we're logged in
    And we add the entry 1.2.3.1/32 with expiration 1970-01-01T00:00:00Z
    And we add the entry 1.2.3.2/32 with expiration 2000-01-01T00:00:00Z
    And we add the entry 1.2.3.3/32 with expiration 2030-01-01T00:00:00Z
    And we add the entry 1.2.3.4/32 with expiration in 12 seconds
    Then the number of entrys is 4
    And 1.2.3.1/32 is announced by block translators
    And 1.2.3.2/32 is announced by block translators
    And 1.2.3.3/32 is announced by block translators
    And 1.2.3.4/32 is announced by block translators
    And we remove expired entries
    And the number of entrys is 2
    And 1.2.3.1/32 is not announced by block translators
    And 1.2.3.3/32 is announced by block translators
    And we wait 12 seconds
    And we remove expired entries
    And the number of entrys is 1

  Scenario: Adding an IP expires after calling process-expiration
    When we're logged in
    And we add the entry 1.2.3.1/32 with expiration 1970-01-01T00:00:00Z
    And we add the entry 1.2.3.2/32 with expiration 2000-01-01T00:00:00Z
    And we add the entry 1.2.3.3/32 with expiration 2030-01-01T00:00:00Z
    Then the number of entrys is 3
    And 1.2.3.1/32 is announced by block translators
    And 1.2.3.3/32 is announced by block translators
    And we remove expired entries
    And the number of entrys is 1
    And 1.2.3.1/32 is not announced by block translators
    And 1.2.3.3/32 is announced by block translators


  Scenario: Adding an IP twice gets expired after the last entry expires
    When we're logged in
    And we add the entry 1.2.3.1/32 with expiration 1970-01-01T00:00:00Z
    And we add the entry 1.2.3.1/32 with expiration 2030-01-01T00:00:00Z
    Then 1.2.3.1/32 is announced by block translators
    And we remove expired entries
    And 1.2.3.1/32 is announced by block translators

  Scenario: Adding an IP twice gets expired after the last entry expires in 2 seconds
    When we're logged in
    And we add the entry 1.2.3.1/32 with expiration 1970-01-01T00:00:00Z
    And we add the entry 1.2.3.1/32 with expiration in 12 seconds
    Then 1.2.3.1/32 is announced by block translators
    And we remove expired entries
    And we wait 1 seconds
    And 1.2.3.1/32 is announced by block translators
    And we wait 13 seconds
    And we remove expired entries
    And 1.2.3.1/32 is not announced by block translators
