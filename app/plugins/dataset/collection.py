from systems.plugins.index import BaseProvider
from utility.data import ensure_list
from utility.query import init_fields, init_filters
from utility.dataframe import merge


class Provider(BaseProvider('dataset', 'collection')):

    def generate_data(self):
        return self.get_combined_collection(
            query_types = self.field_query_fields,
            required_types = self.field_required_types,
            index_field = self.field_index_field,
            merge_fields = self.field_merge_fields,
            remove_fields = self.field_remove_fields,
            column_prefix = self.field_column_prefix,
            processors = self.field_processors
        )


    def get_record(self, data_type,
        index_field = None,
        merge_fields = None,
        remove_fields = None,
        fields = None,
        filters = None,
        order = None
    ):
        fields = init_fields(fields)

        if index_field and index_field not in fields:
            fields.append(index_field)

        return self.command.get_data_item(data_type, *fields,
            filters = init_filters(filters),
            order = order,
            dataframe = True,
            dataframe_index_field = index_field,
            dataframe_merge_fields = merge_fields,
            dataframe_remove_fields = remove_fields
        )

    def get_collection(self, data_type,
        index_field = None,
        merge_fields = None,
        remove_fields = None,
        fields = None,
        filters = None,
        order = None
    ):
        fields = init_fields(fields)

        if index_field and index_field not in fields:
            fields.append(index_field)

        return self.command.get_data_set(data_type, *fields,
            filters = init_filters(filters),
            order = order,
            dataframe = True,
            dataframe_index_field = index_field,
            dataframe_merge_fields = merge_fields,
            dataframe_remove_fields = remove_fields
        )


    def get_combined_collection(self, query_types,
        index_field = None,
        merge_fields = None,
        remove_fields = None,
        column_prefix = True,
        processors = None,
        required_types = None
    ):
        required_types = ensure_list(required_types) if required_types else None
        required_columns = []
        collection = []

        for query_type, params in query_types.items():
            data_type = params.pop('data', query_type)
            prefix = params.pop('column_prefix', column_prefix)
            functions = params.pop('processors', processors)

            collection_method = getattr(self, f"get_{query_type}_collection", None)
            if not collection_method and data_type != query_type:
                collection_method = getattr(self, f"get_{data_type}_collection", None)

            method_params = {
                'index_field': index_field,
                'merge_fields': merge_fields,
                'remove_fields': remove_fields,
                **params
            }

            if collection_method:
                data = collection_method(**method_params)
            else:
                data = self.get_collection(data_type, **method_params)

            if prefix:
                data.columns = [f"{query_type}_{column}" for column in data.columns]

            if functions:
                for function in functions:
                    data = self.exec_data_processor(function, data)

            if required_types and query_type in required_types:
                required_columns.extend(list(data.columns))

            collection.append(data)

        data = merge(*collection,
            required_fields = required_columns,
            ffill = False
        )
        if processors:
            for function in processors:
                data = self.exec_data_processor(function, data)

        return data
