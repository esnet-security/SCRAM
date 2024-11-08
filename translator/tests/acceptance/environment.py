from gobgp import GoBGP


def before_all(context):
    context.gobgp = GoBGP("gobgp:50051")
    context.config.setup_logging()
