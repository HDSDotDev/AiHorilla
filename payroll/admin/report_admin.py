"""
Admin configuration for payroll reports
"""

from django.contrib import admin
from payroll.models.report_models import (
    ReportCategory,
    ReportTemplate,
    ReportSchedule,
    GeneratedReport,
    BankFileConfiguration
)


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'report_type', 'output_format', 'is_active', 'created_at']
    list_filter = ['category', 'report_type', 'output_format', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['accessible_departments']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'report_type', 'description', 'output_format', 'is_active')
        }),
        ('Requirements', {
            'fields': ('requires_date_range', 'requires_company', 'requires_department', 'requires_employee')
        }),
        ('Configuration', {
            'fields': ('columns_config', 'filters_config', 'sorting_config', 'template_path'),
            'classes': ('collapse',)
        }),
        ('Access Control', {
            'fields': ('accessible_by_all', 'accessible_departments')
        }),
    )


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_template', 'frequency', 'is_active', 'next_run_date', 'last_run_date']
    list_filter = ['frequency', 'is_active']
    search_fields = ['name', 'report_template__name']
    fieldsets = (
        ('Schedule Information', {
            'fields': ('name', 'report_template', 'frequency', 'is_active')
        }),
        ('Run Dates', {
            'fields': ('next_run_date', 'last_run_date')
        }),
        ('Email Configuration', {
            'fields': ('email_recipients', 'email_subject', 'email_body')
        }),
        ('Filters', {
            'fields': ('company', 'department')
        }),
    )


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'report_template', 'generated_by', 'status', 'generated_at', 'completed_at']
    list_filter = ['status', 'generated_at', 'report_template']
    search_fields = ['file_name', 'generated_by__employee_first_name', 'generated_by__employee_last_name']
    readonly_fields = ['generated_at', 'completed_at', 'processing_time']
    fieldsets = (
        ('Report Information', {
            'fields': ('report_template', 'generated_by', 'status', 'file_path', 'file_name')
        }),
        ('Filters Used', {
            'fields': ('date_from', 'date_to', 'company', 'department', 'employee')
        }),
        ('Metadata', {
            'fields': ('parameters', 'error_message', 'generated_at', 'completed_at', 'processing_time')
        }),
    )


@admin.register(BankFileConfiguration)
class BankFileConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'bank', 'file_format', 'company', 'is_active']
    list_filter = ['bank', 'file_format', 'is_active']
    search_fields = ['name', 'company__company']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'bank', 'file_format', 'company', 'is_active')
        }),
        ('File Configuration', {
            'fields': ('delimiter', 'include_header', 'date_format', 'file_name_template')
        }),
        ('Field Mapping', {
            'fields': ('field_mapping',)
        }),
    )
