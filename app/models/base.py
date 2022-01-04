class EntityBase(object):

    def to_json(self):
        fields = self.__dict__

        if "_sa_instance_state" in fields:
            del fields["_sa_instance_state"]

        return fields
