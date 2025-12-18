"""
report_urls.py

URL patterns for payroll reporting system
"""

from django.urls import path
from payroll.views import report_views

urlpatterns = [
    # Main dashboard
    path('reports/', report_views.report_dashboard, name='report-dashboard'),
    path('reports/category/<int:category_id>/', report_views.report_category_view, name='report-category-view'),
    path('reports/category/', report_views.report_category_view, name='report-category-view-all'),
    
    # Report generation
    path('reports/generate/<int:report_id>/', report_views.report_generate, name='report-generate'),
    path('reports/history/', report_views.report_history, name='report-history'),
    path('reports/download/<int:report_id>/', report_views.report_download, name='report-download'),
    path('reports/export-data/', report_views.export_report_data, name='export-report-data'),
    
    # Report template management (admin)
    path('reports/templates/', report_views.report_template_list, name='report-template-list'),
    path('reports/templates/create/', report_views.report_template_create, name='report-template-create'),
    path('reports/templates/update/<int:template_id>/', report_views.report_template_update, name='report-template-update'),
    path('reports/templates/delete/<int:template_id>/', report_views.report_template_delete, name='report-template-delete'),
    
    # Bank file configuration
    path('reports/bank-config/', report_views.bank_file_config_list, name='bank-config-list'),
    path('reports/bank-config/create/', report_views.bank_file_config_create, name='bank-config-create'),
    
    # Report scheduling
    path('reports/schedules/', report_views.report_schedule_list, name='report-schedule-list'),
    path('reports/schedules/create/', report_views.report_schedule_create, name='report-schedule-create'),
    
    # AJAX endpoints
    path('reports/api/statistics/', report_views.get_report_statistics, name='report-statistics-api'),
]
