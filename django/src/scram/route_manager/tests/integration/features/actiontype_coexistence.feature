Feature: Issue #258

  Repro for https://github.com/esnet-security/SCRAM/issues/258.

  The WUI expiration field is a plain <input type="datetime-local"> that
  submits naive local time without a timezone, and SCRAM stores naive values
  as UTC (TIME_ZONE="UTC"). Someone in a UTC-6 zone typing "3 minutes from now"
  on their local clock therefore stores an expiration that is already ~6 hours
  in the past, and the next update will notice this and deactivates the entry.

  Scenario: Second entry with a different action type must not remove the first entry
    Given a block actiontype is defined
    And a test actiontype is defined
    And a superuser WUI user exists
    And we are logged in to the WUI on the primary instance
    When we add entry 1.1.1.1 on the WUI with action type block and expiration in 3 minutes entered from a browser 6 hours behind the server
    Then the WUI on the primary instance shows entry 1.1.1.1/32
    And the entry 1.1.1.1/32 with action type block is active in the database
    When primary instance runs process_updates to expire entries
    And we add entry 2.2.2.2 on the WUI with action type test and expiration in 2 minutes entered from a browser 6 hours behind the server
    Then the WUI on the primary instance shows entry 1.1.1.1/32
    And the WUI on the primary instance shows entry 2.2.2.2/32
    And the entry 1.1.1.1/32 with action type block is active in the database
    And the entry 2.2.2.2/32 with action type test is active in the database
