## Environment Variables to Set for Deployment
[comment]: # Which branch of SCRAM to use (you probably want to set it to a release tag)
scram_code_branch:
#### Systems
[comment]: # Email of the main admin
scram_manager_email:
[comment]: # Set to true for production mode; set to false to set up the compose.override.local.yml stack
scram_prod: true
[comment]: # Set to true if you want ansible to install a scram user
scram_install_user: true
[comment]: # What group to put `scram` user in
scram_group: 'scram'
[comment]: # What username to use for `scram` user
scram_user: ''
[comment]: # WHat uid to use for `scram` user
scram_uid: ''
[comment]: # What directory to use for base of the repo
scram_home: '/usr/local/scram'
[comment]: # IP or DNS record for your postgres host
scram_postgres_host:
[comment]: # What postgres user to use
scram_postgres_user: ''

#### Authentication
[comment]: # This chooses if you want to use oidc or local accounts. This can be local or oidc only. Default: `local`
scram_auth_method: "local"
[comment]: # This client id (username) for your oidc connection. Only need to set this if you are trying to do oidc.
scram_oidc_client_id: 

#### Networking
[comment]: # What is the peering interface docker uses for gobgp to talk to the router
scram_peering_iface: 'ens192'
[comment]: # The v6 network of your peering connection
scram_v4_subnet: '10.0.0.0/24'
[comment]: # The v4 IP of the peering connection for the router side
scram_v4_gateway: '10.0.0.1'
[comment]: # The v4 IP of the peering connection for gobgp side
scram_v4_address: '10.0.0.2'
[comment]: # The v6 network of your peering connection
scram_v6_subnet: '2001:db8::/64'
[comment]: # The v6 IP of the peering connection for the router side
scram_v6_gateway: '2001:db8::2'
[comment]: # The v6 IP of the peering connection for the gobgp side
scram_v6_address: '2001:db8::3'
[comment]: # The AS you want to use for gobgp
scram_as: 
[comment]: # A string representing your gobgp instance. Often seen as the local IP of the gobgp instance
scram_router_id:
[comment]: #
scram_peer_as:
[comment]: # The AS you want to use for gobgp side (can this be the same as `scram_as`?)
scram_local_as:
[comment]: # The fqdn of the server hosting this - to be used for nginx
scram_nginx_host:
[comment]: # List of allowed hosts per the django setting "ALLOWED_HOSTS". This should be a list of strings in shell
[comment]: # `django` is required for the websockets to work
[comment]: # Our Ansible assumes `django` + `scram_nginx_host`
scram_django_allowed_hosts: "django"
[comment]: # The fqdn of the server hosting this - to be used for nginx
scram_server_alias:
[comment]: # Do you want to set an md5 for authentication of bgp
scram_bgp_md5_enabled: false
[comment]: # The neighbor config of your gobgp config
scram_neighbors:
[comment]: # The v6 address of your neighbor
  - neighbor_address: 2001:db8::2
[comment]: # This is a v6 address so don't use v4
    ipv4: false
[comment]: # This is a v6 address so use v6
    ipv6: true
[comment]: # The v4 address of your neighbor
  - neighbor_address: 10.0.0.200
[comment]: # This is a v4 address so use v4
    ipv4: true
[comment]: # This is a v4 address so don't use v6
    ipv6: false
