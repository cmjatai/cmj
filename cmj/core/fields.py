from django.core.exceptions import ValidationError
from django.forms.fields import CharField


class CEPFormField(CharField):

    default_error_messages = {
        'invalid': _('CEP é invalido'),
        'required': _('Número de CEP é obrigatório'),
    }

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 9  # count on "-" (hifen) mask character
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            if self.required:
                raise ValidationError(self.error_messages['required'])
        else:
            pass
            # TODO: validar cep
            # if not is_cep(value):
            #    raise ValidationError(self.error_messages['invalid'])

        # return ''.join([d for d in value if d.isdigit()])
        return value
