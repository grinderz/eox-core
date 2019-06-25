"""
Controllers for the data-api. Used in the report generation process
"""
import random
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from edx_proctoring.models import \
    ProctoredExamStudentAttempt  # pylint: disable=import-error
from rest_framework import filters, mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_oauth.authentication import OAuth2Authentication

from eox_core.edxapp_wrapper.certificates import get_generated_certificate
from eox_core.edxapp_wrapper.users import get_course_enrollment

from .filters import (CourseEnrollmentFilter, GeneratedCerticatesFilter,
                      ProctoredExamStudentAttemptFilter, UserFilter)
from .paginators import DataApiResultsSetPagination
from .serializers import (CertificateSerializer, CourseEnrollmentSerializer,
                          ProctoredExamStudentAttemptSerializer,
                          UserSerializer)
from .tasks import EnrollmentsGrades
from .utils import filter_queryset_by_microsite


class DataApiViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    A generic viewset for all the instances of the data-api
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (IsAdminUser,)

    pagination_class = DataApiResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    prefetch_fields = False
    # Microsite enforcement filter settings
    enforce_microsite_filter = False
    enforce_microsite_filter_lookup = "test_lookup"
    enforce_microsite_filter_term = "org_in_course_id"

    def get_queryset(self):
        queryset = self.queryset
        if self.prefetch_fields:
            queryset = self.add_prefetch_fields_to_queryset(queryset, self.prefetch_fields)
        if self.enforce_microsite_filter:
            queryset = self.enforce_microsite_filter_qset(queryset)
        return queryset

    def add_prefetch_fields_to_queryset(self, queryset, fields=None):
        """
        TODO: add me
        """
        if not fields:
            fields = []

        for val in fields:
            if val.get("type", "") == "prefetch":
                queryset = queryset.prefetch_related(val.get("name", ""))
            else:
                queryset = queryset.select_related(val.get("name", ""))

        return queryset

    def enforce_microsite_filter_qset(self, queryset):
        """
        TODO: add-me
        """
        site = self.request.query_params.get('site', None)
        if not site:
            return queryset.none()
        queryset = filter_queryset_by_microsite(
            queryset,
            site,
            self.enforce_microsite_filter_lookup,
            self.enforce_microsite_filter_term
        )
        return queryset


class UsersViewSet(DataApiViewSet):  # pylint: disable=too-many-ancestors
    """
    A viewset for viewing users in the platform.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_class = UserFilter
    prefetch_fields = [
        {
            "name": "profile",
            "type": "select"
        },
        {
            "name": "usersignupsource_set",
            "type": "prefetch"
        }
    ]


class CourseEnrollmentViewset(DataApiViewSet):  # pylint: disable=too-many-ancestors
    """
    A viewset for viewing Course Enrollments.
    """
    serializer_class = CourseEnrollmentSerializer
    queryset = get_course_enrollment().objects.all()
    filter_class = CourseEnrollmentFilter
    # Microsite enforcement filter settings
    enforce_microsite_filter = True
    enforce_microsite_filter_lookup = "course__id__contains"
    enforce_microsite_filter_term = "org_in_course_id"


class CourseEnrollmentWithGradesViewset(DataApiViewSet):  # pylint: disable=too-many-ancestors
    """
    A viewset for viewing Course Enrollments with grades data.
    This view will create a celery task to fetch grades data for
    enrollments in the background, and will return the id of the
    celery task
    """
    serializer_class = CourseEnrollmentSerializer
    queryset = get_course_enrollment().objects.all()
    filter_class = CourseEnrollmentFilter
    # Microsite enforcement filter settings
    enforce_microsite_filter = True
    enforce_microsite_filter_lookup = "course__id__contains"
    enforce_microsite_filter_term = "org_in_course_id"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        now_date = datetime.now()
        string_now_date = now_date.strftime("%Y-%m-%d-%H-%M-%S")
        randnum = random.randint(100, 999)
        task_id = "data_api-" + string_now_date + "-" + str(randnum)

        named_args = {
            "data": serializer.data,
        }

        task = EnrollmentsGrades().apply_async(
            kwargs=named_args,
            task_id=task_id,
            routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY
        )

        url_task_status = request.build_absolute_uri(
            reverse("eox-core:eox-data-api:celery-data-api-tasks", kwargs={"task_id": task_id})
        )
        data_response = {
            "task_id": task.id,
            "task_url": url_task_status,
        }
        return Response(data_response, status=status.HTTP_202_ACCEPTED)


class CertificateViewSet(DataApiViewSet):  # pylint: disable=too-many-ancestors
    """
    A viewset for viewing certificates generated for users.
    """
    serializer_class = CertificateSerializer
    queryset = get_generated_certificate().objects.all()
    filter_class = GeneratedCerticatesFilter
    prefetch_fields = [
        {
            "name": "user",
            "type": "select"
        }
    ]
    # Microsite enforcement filter settings
    enforce_microsite_filter = True
    enforce_microsite_filter_lookup = "course_id__contains"
    enforce_microsite_filter_term = "org_in_course_id"


class ProctoredExamStudentViewSet(DataApiViewSet):  # pylint: disable=too-many-ancestors
    """
    A viewset for viewing proctored exams attempts made by students.
    """

    serializer_class = ProctoredExamStudentAttemptSerializer
    queryset = ProctoredExamStudentAttempt.objects.all()
    filter_class = ProctoredExamStudentAttemptFilter
    prefetch_fields = [
        {
            "name": "user",
            "type": "select"
        },
        {
            "name": "proctored_exam",
            "type": "select"
        }
    ]
    # Microsite enforcement filter settings
    enforce_microsite_filter = True
    enforce_microsite_filter_lookup = "proctored_exam__course_id__contains"
    enforce_microsite_filter_term = "org_in_course_id"
