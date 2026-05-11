Feature: Multi-Instance Synchronization

  Scenario: Entry created on primary syncs to secondary (IPv4)
    Given a block actiontype is defined
    When we create an entry 192.0.2.1/32 on primary instance
    And we wait for database commit
    When secondary instance runs process_updates
    Then secondary announces 192.0.2.1/32 addition to block translators

  Scenario: Entry created on primary syncs to secondary (IPv6)
    Given a block actiontype is defined
    When we create an entry 2001:db8::10/128 on primary instance
    And we wait for database commit
    When secondary instance runs process_updates
    Then secondary announces 2001:db8::10/128 addition to block translators

  Scenario: Entry expired on primary syncs removal to secondary (IPv4)
    Given a block actiontype is defined
    When we create entry 192.0.2.2/32 with 1 second expiration on primary instance
    And we wait 2 seconds for expiration
    When primary instance runs process_updates to expire entries
    And we wait for database commit
    When secondary instance runs process_updates
    Then the entry 192.0.2.2/32 is inactive on secondary instance
    And secondary announces 192.0.2.2/32 removal to block translators

  Scenario: Entry expired on primary syncs removal to secondary (IPv6)
    Given a block actiontype is defined
    When we create entry 2001:db8::20/128 with 1 second expiration on primary instance
    And we wait 2 seconds for expiration
    When primary instance runs process_updates to expire entries
    And we wait for database commit
    When secondary instance runs process_updates
    Then the entry 2001:db8::20/128 is inactive on secondary instance
    And secondary announces 2001:db8::20/128 removal to block translators

  Scenario: Entry deactivated on primary syncs to secondary (IPv4)
    Given a block actiontype is defined
    When we create an entry 192.0.2.3/32 on primary instance
    And we deactivate entry 192.0.2.3/32 on primary instance
    And we wait for database commit
    When secondary instance runs process_updates
    Then the entry 192.0.2.3/32 is inactive on secondary instance
    And secondary announces 192.0.2.3/32 removal to block translators

  Scenario: Entry deactivated on primary syncs to secondary (IPv6)
    Given a block actiontype is defined
    When we create an entry 2001:db8::30/128 on primary instance
    And we deactivate entry 2001:db8::30/128 on primary instance
    And we wait for database commit
    When secondary instance runs process_updates
    Then the entry 2001:db8::30/128 is inactive on secondary instance
    And secondary announces 2001:db8::30/128 removal to block translators

  Scenario: IPv4 entry expiring on primary instance is reprocessed by primary
    Given a block actiontype is defined
    When we create entry 192.168.100.4/32 with 3 second expiration on primary instance
    And we wait for database commit
    And we wait 4 seconds for expiration
    When primary instance runs process_updates to expire entries
    Then primary announces 192.168.100.4/32 removal to block translators

  Scenario: IPv6 entry expiring on primary instance is reprocessed by primary
    Given a block actiontype is defined
    When we create entry 2001:db8::4/128 with 3 second expiration on primary instance
    And we wait for database commit
    And we wait 4 seconds for expiration
    When primary instance runs process_updates to expire entries
    Then primary announces 2001:db8::4/128 removal to block translators

  Scenario: IPv4 entry deactivated on primary instance is reprocessed by primary
    Given a block actiontype is defined
    When we create an entry 192.168.100.5/32 on primary instance
    And we wait for database commit
    When we deactivate entry 192.168.100.5/32 on primary instance
    And we wait for database commit
    When primary instance runs process_updates to expire entries
    Then primary announces 192.168.100.5/32 removal to block translators

  Scenario: IPv6 entry deactivated on primary instance is reprocessed by primary
    Given a block actiontype is defined
    When we create an entry 2001:db8::5/128 on primary instance
    And we wait for database commit
    When we deactivate entry 2001:db8::5/128 on primary instance
    And we wait for database commit
    When primary instance runs process_updates to expire entries
    Then primary announces 2001:db8::5/128 removal to block translators
