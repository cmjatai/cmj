from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _
from image_cropping import ImageCroppingMixin

from cmj.utils import register_all_models_in_admin

from .forms import UserChangeForm, UserCreationForm
from .models import User


# Register your models here.
class UserAdmin(BaseUserAdmin, ImageCroppingMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
         'fields': ('first_name', 'last_name', 'avatar', 'cropping')}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(get_user_model(), UserAdmin)

register_all_models_in_admin(__name__)
