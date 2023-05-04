from systems.models.base import DatabaseAccessError
from systems.models.index import BaseModel
from utility.data import get_identifier


class IdentifierResourceBase(BaseModel('id_resource')):

    def save(self, *args, **kwargs):
        self._prepare_save()
        self.get_id()
        super().save(*args, **kwargs)


    def get_id_values(self):
        values = []
        fields = sorted(self.get_id_fields())
        if not fields:
            fields = [ 'name' ]

        for field in fields:
            value = getattr(self, field, None)

            if value is None:
                raise DatabaseAccessError(f"Field {field} does not exist in model {str(self)}")
            if field == 'created':
                value = value.strftime("%Y%m%d%H%M%S%f")

            values.append(str(value))
        return values

    def get_id(self):
        if not self.id:
            self._set_created_time()
            self.id = get_identifier(self.get_id_values())
        return self.id
