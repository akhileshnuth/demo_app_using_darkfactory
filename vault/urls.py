# Include the path for exporting data
from .views import ExportView

urlpatterns += [
    path(
        'export/',
        ExportView.as_view(),
        name='export_data',
    ),
]