from rest_framework import routers, serializers, viewsets
from rest_framework.pagination import PageNumberPagination

from govscentdotorg.models import Bill, BillTopic


class BillSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Bill
        fields = '__all__'


class BillViewSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().order_by('id')
    serializer_class = BillSerializer
    pagination_class = BillViewSetPagination


class BillTopicSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = BillTopic
        fields = '__all__'


class BillTopicViewSet(viewsets.ModelViewSet):
    queryset = BillTopic.objects.all().order_by('id')
    serializer_class = BillTopicSerializer


api_router = routers.DefaultRouter()
api_router.register(r'bills/v1', BillViewSet)
api_router.register(r'bill_topics/v1', BillTopicViewSet)
