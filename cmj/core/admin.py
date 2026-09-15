from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from image_cropping.admin import ImageCroppingMixin

from cmj.core.forms_auth import UserChangeForm, UserCreationForm
from cmj.core.models import IAQuota
from cmj.utils import register_all_models_in_admin


# Register your models here.
class UserAdmin(BaseUserAdmin, ImageCroppingMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "avatar", "cropping")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )


class IAQuotaAdmin(admin.ModelAdmin):
    """customiza o field servicos_autorizados que é um ArrayField"""

    class IAQuotaForm(forms.ModelForm):
        servicos_autorizados = forms.TypedMultipleChoiceField(
            label=_("Serviços Autorizados"),
            coerce=str,
            choices=IAQuota.ServicosAutorizados.choices,
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )

        descricao = forms.CharField(
            label=_("Descrição"),
            widget=forms.Textarea(attrs={"rows": 25}),
            required=False,
        )

        class Meta:
            model = IAQuota
            fields = "__all__"

    form = IAQuotaForm

    list_display = (
        "quota_diaria",
        "modelo",
        "ativo",
        "batch_size",
        "get_threads",
        "str_remaining_quota",
        "servicos_autorizados",
    )


admin.site.register(get_user_model(), UserAdmin)

admin.site.register(IAQuota, IAQuotaAdmin)
register_all_models_in_admin(__name__)
