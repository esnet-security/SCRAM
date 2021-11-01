import walrus


def before_all(context):
    context.db = walrus.Database(host="redis")
