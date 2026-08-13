from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import (
    ChecklistInstance,
    ChecklistItem,
    ChecklistItemAttachment,
    ChecklistItemResponse,
    ChecklistSection,
    ChecklistTemplate,
    ItemOption,
)


class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = ["title", "description", "version", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ChecklistSectionForm(forms.ModelForm):
    # `template` é preenchido automaticamente pelo MasterDetailCrud a partir da URL.
    class Meta:
        model = ChecklistSection
        fields = ["title", "description", "order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ChecklistItemForm(forms.ModelForm):
    # `section` é preenchido automaticamente pelo MasterDetailCrud a partir da URL.
    class Meta:
        model = ChecklistItem
        fields = ["label", "description", "response_type", "is_mandatory", "order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ItemOptionForm(forms.ModelForm):
    # `item` é preenchido automaticamente pelo MasterDetailCrud a partir da URL.
    class Meta:
        model = ItemOption
        fields = ["text", "order"]


class ChecklistInstanceForm(forms.ModelForm):
    # content_type/object_id expostos como campos simples por ora; uma seleção
    # dedicada por tipo de entidade (Organization, Project, etc.) fica para
    # uma etapa futura.
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model")
    )

    class Meta:
        model = ChecklistInstance
        fields = ["template", "content_type", "object_id", "status", "submitted_at"]


class ChecklistItemResponseForm(forms.ModelForm):
    # `instance` é preenchido automaticamente pelo MasterDetailCrud a partir da URL.
    class Meta:
        model = ChecklistItemResponse
        fields = [
            "item",
            "text_value",
            "boolean_value",
            "date_value",
            "selected_options",
            "validation_status",
            "validation_notes",
            "validated_at",
        ]
        widgets = {
            "text_value": forms.Textarea(attrs={"rows": 3}),
            "validation_notes": forms.Textarea(attrs={"rows": 3}),
        }


class ChecklistItemAttachmentForm(forms.ModelForm):
    # `response` é preenchido automaticamente pelo MasterDetailCrud a partir da URL.
    class Meta:
        model = ChecklistItemAttachment
        fields = ["file", "description"]
