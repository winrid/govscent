from rest_framework import routers, serializers, viewsets
from rest_framework.pagination import PageNumberPagination

from govscentdotorg.models import Bill, BillTopic, BillSection, BillSmell


class SmallViewSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


class BillSectionSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = BillSection
        fields = '__all__'


class BillSectionViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().order_by('id')
    serializer_class = BillSectionSerializer
    pagination_class = SmallViewSetPagination


class BillSmellSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = BillSmell
        fields = '__all__'


class BillSmellViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().order_by('id')
    serializer_class = BillSmellSerializer
    pagination_class = SmallViewSetPagination


class BillSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Bill
        fields = '__all__'


class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().order_by('id')
    serializer_class = BillSerializer
    pagination_class = SmallViewSetPagination


class BillTopicSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = BillTopic
        fields = '__all__'


class BillTopicViewSet(viewsets.ModelViewSet):
    queryset = BillTopic.objects.all().order_by('id')
    serializer_class = BillTopicSerializer


class RouterRootView(routers.APIRootView):
    """
    Welcome to the Govscent API! The below resources are read-only for public users, and paginated based on id.
    """


class Router(routers.DefaultRouter):
    APIRootView = RouterRootView


api_router = Router()
api_router.register(r'bills/v1', BillViewSet)
api_router.register(r'bill_topics/v1', BillTopicViewSet)
api_router.register(r'bill_sections/v1', BillSectionViewSet)
api_router.register(r'bill_smells/v1', BillSmellViewSet)
