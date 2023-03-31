from rest_framework import mixins, viewsets


class ReadOrListOnlyViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    pass


class ListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pass
