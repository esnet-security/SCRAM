Feature: remove a network
  Users can remove a v4 and v6 network

  Scenario: unauthenticated users get a 403
    When we add the entry 127.0.0.1
    Then we get a 403 status code

  Scenario Outline: removing a nonexistant IP returns a 404
    When we're logged in
    And we remove the entry <IP>
    Then we get a 404 status code

    Examples: v4 IPs
      | IP            |
      | 1.2.3.4       |
      | 5.6.7.8/32    |
      | 22.22.22.1/24 |

    Examples: v6 IPs
      | IP            |
      | 2000::        |
      | ::1/128       |
      | 2000::1/8     |

  Scenario Outline: removing an existing IP returns a 204
    When we're logged in
    And we add the entry <IP>
    And we remove the entry <IP>
    Then we get a 204 status code
    And the number of IPs is 0

    Examples: v4 IPs
      | IP            |
      | 1.2.3.4       |
      | 5.6.7.8/32    |
      | 22.22.22.1/24 |

    Examples: v6 IPs
      | IP            |
      | 2000::        |
      | ::1/128       |
      | 2000::1/8     |
