class SubFuncaoViewSet:

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        qp = self.request.query_params
        if "despesa_set__isnull" in qp:
            dsisnull = qp["despesa_set__isnull"] == "true"
            qs = qs.filter(despesa_set__isnull=dsisnull).order_by("codigo").distinct()

        return qs
