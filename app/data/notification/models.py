from systems.models.index import Model, ModelFacade


class NotificationFacade(ModelFacade('notification')):

    def get_field_group_names_display(self, instance, value, short):
        display = [record.group.name for record in instance.groups.all()]
        return super().get_field_group_names_display(instance, "\n".join(display) + "\n", short)

    def get_field_failure_group_names_display(self, instance, value, short):
        display = [record.group.name for record in instance.failure_groups.all()]
        return super().get_field_failure_group_names_display(instance, "\n".join(display) + "\n", short)
