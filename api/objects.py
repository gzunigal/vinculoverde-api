
class ProductCreationTransaction(object):
  def __init__(self, **kwargs):
    for field in ('id', 'name', 'owner', 'status'):
      setattr(self, field, kwargs.get(field, None))
