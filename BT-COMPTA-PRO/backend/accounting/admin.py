from django.contrib import admin

from .models import Account, AccountingRule, Company, EntryLine, FiscalYear, Journal, JournalEntry, PlanVersion, TaxRate


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'account_class', 'company', 'verified', 'is_active')
    list_filter = ('account_class', 'verified', 'is_active')
    search_fields = ('code', 'label')


class EntryLineInline(admin.TabularInline):
    model = EntryLine
    extra = 0


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'journal', 'number', 'label', 'status', 'company')
    list_filter = ('status', 'journal__code')
    inlines = [EntryLineInline]

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.is_locked) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.is_locked) and super().has_delete_permission(request, obj)


admin.site.register([PlanVersion, TaxRate, AccountingRule, Company, FiscalYear, Journal])
