"""A translator interface for GoBGP (https://github.com/osrg/gobgp)."""

import logging

import grpc
from api import attribute_pb2, common_pb2, gobgp_pb2, gobgp_pb2_grpc, nlri_pb2, extcom_pb2

from .exceptions import ASNError
from .settings import settings
from .shared import asn_is_valid

_TIMEOUT_SECONDS = 1000
MAX_SMALL_ASN = 2**16
MAX_SMALL_COMM = 2**16
IPV4 = 4
IPV6 = 6

logger = logging.getLogger(__name__)

# Temporary list to keep track of active flowspec rules.
_active_rules = []


class GoBGP:
    """Represents a GoBGP instance."""

    def __init__(self, url):
        """Configure the channel used for communication."""
        channel = grpc.insecure_channel(url)
        self.stub = gobgp_pb2_grpc.GoBgpServiceStub(channel)

    @staticmethod
    def _family(ip_version):
        afi = common_pb2.Family.AFI_IP6 if ip_version == IPV6 else common_pb2.Family.AFI_IP
        return common_pb2.Family(afi=afi, safi=common_pb2.Family.SAFI_UNICAST)

    def _build_path(self, ip, event_data=None):  # noqa: PLR0914
        # Grab ASN and Community from our event_data, or use the defaults
        if not event_data:
            event_data = {}
        asn = event_data.get("asn", settings.default_asn)
        community = event_data.get("community", settings.default_community)
        ip_version = ip.ip.version
        family = self._family(ip_version)

        # Make sure our asn is an acceptable value.
        asn_is_valid(asn)

        # Set the origin to incomplete (options are IGP, EGP, incomplete)
        # Incomplete means that BGP is unsure of exactly how the prefix was injected into the topology.
        # The most common scenario here is that the prefix was redistributed into Border Gateway Protocol
        # from some other protocol, typically an IGP. - https://www.kwtrain.com/blog/bgp-pt2
        origin = attribute_pb2.Attribute(origin=attribute_pb2.OriginAttribute(origin=2))

        # IP prefix and its associated length
        nlri = nlri_pb2.NLRI(
            prefix=nlri_pb2.IPAddressPrefix(prefix_len=ip.network.prefixlen, prefix=str(ip.ip)),
        )

        # Set the next hop to the correct value depending on IP family
        if ip_version == IPV6:
            next_hops = event_data.get("next_hop", settings.default_v6_nexthop)
            next_hop = attribute_pb2.Attribute(
                mp_reach=attribute_pb2.MpReachNLRIAttribute(
                    family=family,
                    next_hops=[next_hops],
                    nlris=[nlri],
                ),
            )
        else:
            next_hops = event_data.get("next_hop", settings.default_v4_nexthop)
            next_hop = attribute_pb2.Attribute(
                next_hop=attribute_pb2.NextHopAttribute(
                    next_hop=next_hops,
                ),
            )

        # Set our AS Path
        as_segment = [attribute_pb2.AsSegment(type=attribute_pb2.AsSegment.TYPE_AS_SEQUENCE, numbers=[asn])]
        as_segments = attribute_pb2.AsPathAttribute(segments=as_segment)
        as_path = attribute_pb2.Attribute(as_path=as_segments)

        # Set our community number
        # The ASN gets packed into the community so we need to be careful about size to not overflow the structure
        # Standard community
        # Since we pack both into the community string we need to make sure they will both fit
        if asn < MAX_SMALL_ASN and community < MAX_SMALL_COMM:
            # We bitshift ASN left by 16 so that there is room to add the community on the end of it. This is because
            # GoBGP wants the community sent as a single integer.
            comm_id = (asn << 16) + community
            communities = attribute_pb2.Attribute(
                communities=attribute_pb2.CommunitiesAttribute(communities=[comm_id]),
            )
        else:
            logger.info("LargeCommunity Used - ASN: %s. Community: %s", asn, community)
            global_admin = asn
            local_data1 = community
            # set to 0 because there's no use case for it, but we need a local_data2 for gobgp to read any of it
            local_data2 = 0
            large_community = attribute_pb2.LargeCommunity(
                global_admin=global_admin,
                local_data1=local_data1,
                local_data2=local_data2,
            )
            communities = attribute_pb2.Attribute(
                large_communities=attribute_pb2.LargeCommunitiesAttribute(communities=[large_community]),
            )

        attributes = [origin, next_hop, as_path, communities]

        return gobgp_pb2.Path(
            nlri=nlri,
            pattrs=attributes,
            family=family,
        )

    def add_path(self, ip, event_data):
        """Announce a single route."""
        logger.info("Blocking %s", ip)
        try:
            path = self._build_path(ip, event_data)

            self.stub.AddPath(
                gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.TABLE_TYPE_GLOBAL, path=path),
                _TIMEOUT_SECONDS,
            )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

    def _build_flowspec_path(self, source_ip, dest_ip, data: dict):
        """Constructs a Flowspec path based on dictionary matches and returns it."""
        rules = []

        _OP_EQ = 0x01
        _OP_END = 0x80

        if dest_ip is not None:
            rules.append(nlri_pb2.FlowSpecRule(
                ip_prefix=nlri_pb2.FlowSpecIPPrefix(
                    type=1, # TYPE_DST_PREFIX
                    prefix_len=dest_ip.network.prefixlen,
                    prefix=dest_ip.network.network_address.exploded,
                )
            ))

        if source_ip is not None:
            rules.append(nlri_pb2.FlowSpecRule(
                ip_prefix=nlri_pb2.FlowSpecIPPrefix(
                    type=2, # TYPE_SRC_PREFIX
                    prefix_len=source_ip.network.prefixlen,
                    prefix=source_ip.network.network_address.exploded,
                )
            ))

        if "protocol" in data:
            rules.append(nlri_pb2.FlowSpecRule(
                component=nlri_pb2.FlowSpecComponent(
                    type=3, # TYPE_PROTOCOL
                    items=[nlri_pb2.FlowSpecComponentItem(
                        op=_OP_END | _OP_EQ,
                        value=int(data["protocol"]),
                    )],
                )
            ))

        if "source-port" in data:
            rules.append(nlri_pb2.FlowSpecRule(
                component=nlri_pb2.FlowSpecComponent(
                    type=6, # TYPE_SRC_PORT
                    items=[nlri_pb2.FlowSpecComponentItem(
                        op=_OP_END | _OP_EQ,
                        value=int(data["source-port"]),
                    )],
                )
            ))

        if "destination-port" in data:
            rules.append(nlri_pb2.FlowSpecRule(
                component=nlri_pb2.FlowSpecComponent(
                    type=5, # TYPE_DST_PORT
                    items=[nlri_pb2.FlowSpecComponentItem(
                        op=_OP_END | _OP_EQ,
                        value=int(data["destination-port"]),
                    )],
                )
            ))

        # Build FlowSpec NLRI
        nlri = nlri_pb2.NLRI(
            flow_spec=nlri_pb2.FlowSpecNLRI(rules=rules)
        )

        attributes = [
            attribute_pb2.Attribute(
                origin=attribute_pb2.OriginAttribute(origin=0)
            )
        ]

        # Build action
        action = data.get("action")
        action_community = None

        if action == "discard":
            action_community = extcom_pb2.ExtendedCommunity(
                traffic_rate=extcom_pb2.TrafficRateExtended(rate=0.0)
            )
        elif action == "rate-limit":
            rate = float(data.get("rate", 0.0))
            action_community = extcom_pb2.ExtendedCommunity(
                traffic_rate=extcom_pb2.TrafficRateExtended(rate=rate)
            )

        if action_community is not None:
            attributes.append(
                attribute_pb2.Attribute(
                    extended_communities=attribute_pb2.ExtendedCommunitiesAttribute(
                        communities=[action_community]
                    )
                )
            )

        if (source_ip and source_ip.version == 6) or (dest_ip and dest_ip.version == 6):
            family_afi = common_pb2.Family.AFI_IP6
        else:
            family_afi = common_pb2.Family.AFI_IP

        # Append mandatory NextHop
        next_hop_ip = "0.0.0.0"
        attributes.append(
            attribute_pb2.Attribute(
                next_hop=attribute_pb2.NextHopAttribute(next_hop=next_hop_ip)
            )
        )

        family = common_pb2.Family(
            afi=family_afi,
            safi=common_pb2.Family.SAFI_FLOW_SPEC_UNICAST,
        )

        path = gobgp_pb2.Path(
            nlri=nlri,
            pattrs=attributes,
            family=family,
        )

        return path

    def add_flowspec(self, source_ip, dest_ip, data: dict):
        """Adds a FlowSpec path to the GoBGP Rib."""
        path = self._build_flowspec_path(source_ip, dest_ip, data)
        serialized_path = path.SerializeToString(deterministic=True)

        response = self.stub.AddPath(
            gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.TABLE_TYPE_GLOBAL, path=path),
            _TIMEOUT_SECONDS
        )

        _active_rules.append(serialized_path)

        return response.uuid.hex()

    def check_flowspec(self, source_ip, dest_ip, data: dict):
        """Checks if a FlowSpec path is currently active in the GoBGP Rib."""
        path = self._build_flowspec_path(source_ip, dest_ip, data)
        serialized_path = path.SerializeToString(deterministic=True)

        return serialized_path in _active_rules

    def del_flowspec(self, source_ip, dest_ip, data: dict):
        """Deletes a FlowSpec path from the GoBGP Rib."""
        path = self._build_flowspec_path(source_ip, dest_ip, data)
        serialized_path = path.SerializeToString(deterministic=True)

        if serialized_path not in _active_rules:
            logger.warning("Attempted to delete a FlowSpec path that is not active: %s", serialized_path)
            return None

        response = self.stub.DeletePath(
            gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.TABLE_TYPE_GLOBAL, path=path),
            _TIMEOUT_SECONDS
        )

        _active_rules.remove(serialized_path)

    def del_all_paths(self):
        """Remove all routes from being announced."""
        logger.warning("Withdrawing ALL routes")

        # GoBGP v4 needs an address family set to be able to delete all prefixes for that family.
        for ip_version in (IPV4, IPV6):
            self.stub.DeletePath(
                gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.TABLE_TYPE_GLOBAL, family=self._family(ip_version)),
                _TIMEOUT_SECONDS,
            )

    def del_path(self, ip, event_data):
        """Remove a single route from being announced."""
        logger.info("Unblocking %s", ip)
        try:
            path = self._build_path(ip, event_data)
            self.stub.DeletePath(
                gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.TABLE_TYPE_GLOBAL, path=path),
                _TIMEOUT_SECONDS,
            )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

    def get_prefixes(self, ip):
        """Retrieve the routes that match a prefix and are announced.

        Returns:
            list: The routes that overlap with the prefix and are currently announced.
        """
        prefixes = [gobgp_pb2.TableLookupPrefix(prefix=str(ip.ip))]
        result = self.stub.ListPath(
            gobgp_pb2.ListPathRequest(
                table_type=gobgp_pb2.TABLE_TYPE_GLOBAL,
                prefixes=prefixes,
                family=self._family(ip.ip.version),
            ),
            _TIMEOUT_SECONDS,
        )
        return list(result)

    def get_route_count(self, ip_version):
        """Return the number of routes in the global RIB for a given IP version."""
        try:
            result = list(
                self.stub.ListPath(
                    gobgp_pb2.ListPathRequest(
                        table_type=gobgp_pb2.TABLE_TYPE_GLOBAL,
                        family=self._family(ip_version),
                    ),
                    _TIMEOUT_SECONDS,
                )
            )
            logger.info("GoBGP returned %d routes for IPv%s", len(result), ip_version)
            return len(result)
        except Exception:
            logger.exception("Failed to get route count for IPv%s", ip_version)
            return 0

    def is_blocked(self, ip):
        """Return True if at least one route matching the prefix is being announced."""
        return len(self.get_prefixes(ip)) > 0
