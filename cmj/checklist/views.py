from sapl.crud.base import Crud, MasterDetailCrud

from .forms import (
    ChecklistInstanceForm,
    ChecklistItemAttachmentForm,
    ChecklistItemForm,
    ChecklistItemResponseForm,
    ChecklistSectionForm,
    ChecklistTemplateForm,
    ItemOptionForm,
)
from .models import (
    ChecklistInstance,
    ChecklistItem,
    ChecklistItemAttachment,
    ChecklistItemResponse,
    ChecklistSection,
    ChecklistTemplate,
    ItemOption,
)


class ChecklistTemplateCrud(Crud):
    model = ChecklistTemplate

    class CreateView(Crud.CreateView):
        form_class = ChecklistTemplateForm

    class UpdateView(Crud.UpdateView):
        form_class = ChecklistTemplateForm


class ChecklistSectionCrud(MasterDetailCrud):
    model = ChecklistSection
    parent_field = "template"

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ChecklistSectionForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ChecklistSectionForm


class ChecklistItemCrud(MasterDetailCrud):
    model = ChecklistItem
    parent_field = "section"

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ChecklistItemForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ChecklistItemForm


class ItemOptionCrud(MasterDetailCrud):
    model = ItemOption
    parent_field = "item"

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ItemOptionForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ItemOptionForm


class ChecklistInstanceCrud(Crud):
    model = ChecklistInstance

    class CreateView(Crud.CreateView):
        form_class = ChecklistInstanceForm

    class UpdateView(Crud.UpdateView):
        form_class = ChecklistInstanceForm


class ChecklistItemResponseCrud(MasterDetailCrud):
    model = ChecklistItemResponse
    parent_field = "instance"

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ChecklistItemResponseForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ChecklistItemResponseForm


class ChecklistItemAttachmentCrud(MasterDetailCrud):
    model = ChecklistItemAttachment
    parent_field = "response"

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ChecklistItemAttachmentForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ChecklistItemAttachmentForm
