"""
URLs for the Microsite API
"""
from django.conf.urls import url, include

from .routers import ROUTER
from .views import CeleryTasksStatus


urlpatterns = [  # pylint: disable=invalid-name
    url(r'^v1/', include((ROUTER.urls, 'eox_core'), namespace='eox-data-api-v1')),
    url(r'^v1/tasks/(?P<task_id>.*)$', CeleryTasksStatus.as_view(), name="celery-data-api-tasks"),
]
