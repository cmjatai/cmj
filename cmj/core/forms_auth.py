from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm,\
    SetPasswordForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from image_cropping.widgets import ImageCropWidget, CropWidget
from sapl.crispy_layout_mixin import to_row, form_actions, SaplFormLayout


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Username", max_length=254,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'name': 'username',
                'placeholder': _('Digite seu Endereço de email')}))
    password = forms.CharField(
        label="Password", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'name': 'password',
                'placeholder': _('Digite sua Senha')}))


class CustomImageCropWidget(ImageCropWidget):
    """
    Custom ImageCropWidget that doesn't show the initial value of the field.
    We use this trick, and place it right under the CropWidget so that
    it looks like the user is seeing the image and clearing the image.
    """
    template_with_initial = (
        # '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )


class CmjUserChangeForm(ModelForm):

    error_messages = {
        'password_mismatch': _("As senhas informadas são diferentes"),
    }
    old_password = forms.CharField(
        label='Senha atual',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput())
    new_password1 = forms.CharField(
        label='Nova senha',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput())
    new_password2 = forms.CharField(
        label='Confirmar senha',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput())

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'avatar', 'cropping',
                  'old_password', 'new_password1', 'new_password2']

        widgets = {
            'avatar': CustomImageCropWidget(),
            'cropping': CropWidget(),
        }

    def __init__(self, *args, **kwargs):

        super(CmjUserChangeForm, self).__init__(*args, **kwargs)
        row0 = to_row([
            ('first_name', 6),
            ('last_name', 6),
        ])
        row1 = to_row([
            ('old_password', 12)
        ])
        row2 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])
        row3 = to_row(
            [('avatar', 6),
             ('cropping', 6)])

        rows = [row0]
        if self.instance.pwd_created:
            rows.append(row1)

        rows += [row2, row3]

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(*rows)

        if not self.instance.pwd_created:
            self.fields['old_password'].widget = forms.HiddenInput()

    def save(self, commit=True):
        new_password = self.cleaned_data['new_password1']

        user = self.instance

        if new_password:
            user.set_password(new_password)
            user.pwd_created = True

        return super().save(commit)

    def clean(self):
        data = super().clean()

        if self.errors:
            return data

        old_password = data.get('old_password', '')
        new_password1 = data.get('new_password1', '')
        new_password2 = data.get('new_password2', '')

        if old_password and self.instance.pwd_created:
            if not self.instance.check_password(old_password):
                raise ValidationError("Senha atual informada não confere "
                                      "com a senha armazenada")
            if self.instance.check_password(new_password1):
                raise ValidationError(
                    "Nova senha não pode ser igual à senha anterior")

        if new_password1 != new_password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        else:
            if new_password1 and new_password2:
                password_validation.validate_password(
                    new_password2, self.instance)


class UserForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        fields = ('first_name', 'last_name', 'avatar', 'cropping')
        widgets = {
            'avatar': CustomImageCropWidget(),
            'cropping': CropWidget(),
        }


class RecuperarSenhaForm(PasswordResetForm):

    def __init__(self, *args, **kwargs):
        row1 = to_row(
            [('email', 12)])
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Insira o e-mail cadastrado com a sua conta'),
                     row1,
                     form_actions(label='Enviar'))
        )

        super(RecuperarSenhaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(RecuperarSenhaForm, self).clean()

        email_existente = get_user_model().objects.filter(
            email=self.data['email']).exists()

        if not email_existente:
            msg = 'Não existe nenhum usuário cadastrado com este e-mail.'
            raise ValidationError(msg)

        return self.cleaned_data


class NovaSenhaForm(SetPasswordForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(NovaSenhaForm, self).__init__(user, *args, **kwargs)

        row1 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            row1,
            form_actions(label='Enviar'))
