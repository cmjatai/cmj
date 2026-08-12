"""
App `checklist`: biblioteca isolada para checklists dinâmicos aplicáveis a
qualquer entidade do projeto (Organizations, Projects, Users, etc.) via
GenericForeignKey.

Regra de desacoplamento: este módulo não importa nenhum outro app custom do
projeto (nem `cmj.*` nem `sapl.*`). Apenas Django/DRF core e contenttypes.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditableModel(models.Model):
    """Base abstrata de auditoria (multi-tenant friendly, sem FK para outros apps custom)."""

    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Criado por"),
        related_name="%(app_label)s_%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Atualizado por"),
        related_name="%(app_label)s_%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class TemplateStatus(models.TextChoices):
    ACTIVE = "active", _("Ativo")
    INACTIVE = "inactive", _("Inativo")


class ResponseType(models.TextChoices):
    """Extensível: para novos tipos, adicionar aqui e tratar em ChecklistItemResponse."""

    SHORT_TEXT = "short_text", _("Texto Curto")
    LONG_TEXT = "long_text", _("Texto Longo")
    BOOLEAN = "boolean", _("Booleano (Sim/Não)")
    SINGLE_CHOICE = "single_choice", _("Múltipla Escolha (uma resposta)")
    MULTIPLE_CHOICE = "multiple_choice", _("Múltipla Escolha (várias respostas)")
    FILE_UPLOAD = "file_upload", _("Upload de Arquivo")
    DATE = "date", _("Data")


# Tipos que dependem de ItemOption
CHOICE_RESPONSE_TYPES = (ResponseType.SINGLE_CHOICE, ResponseType.MULTIPLE_CHOICE)


class InstanceStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", _("Em preenchimento")
    SUBMITTED = "submitted", _("Enviado")
    APPROVED = "approved", _("Aprovado")
    PENDING = "pending", _("Com Pendências")


class ResponseValidationStatus(models.TextChoices):
    PENDING = "pending", _("Pendente de Análise")
    APPROVED = "approved", _("Aprovado")
    REJECTED = "rejected", _("Reprovado")


class ChecklistTemplate(AuditableModel):
    title = models.CharField(_("Título"), max_length=255)
    description = models.TextField(_("Descrição"), blank=True, default="")
    version = models.PositiveIntegerField(_("Versão"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TemplateStatus.choices,
        default=TemplateStatus.ACTIVE,
    )

    class Meta:
        ordering = ("title", "-version")
        verbose_name = _("Template de Checklist")
        verbose_name_plural = _("Templates de Checklist")

    def __str__(self):
        return f"{self.title} (v{self.version})"


class ChecklistSection(AuditableModel):
    template = models.ForeignKey(
        ChecklistTemplate,
        verbose_name=_("Template"),
        related_name="sections",
        on_delete=models.CASCADE,
    )
    title = models.CharField(_("Título"), max_length=255)
    description = models.TextField(_("Descrição"), blank=True, default="")
    order = models.PositiveIntegerField(_("Ordem"), default=0)

    class Meta:
        ordering = ("template", "order", "id")
        verbose_name = _("Seção do Checklist")
        verbose_name_plural = _("Seções do Checklist")

    def __str__(self):
        return f"{self.template} / {self.title}"


class ChecklistItem(AuditableModel):
    section = models.ForeignKey(
        ChecklistSection,
        verbose_name=_("Seção"),
        related_name="items",
        on_delete=models.CASCADE,
    )
    label = models.CharField(_("Pergunta/Requisito"), max_length=500)
    description = models.TextField(_("Ajuda/Instrução"), blank=True, default="")
    response_type = models.CharField(
        _("Tipo de Resposta"),
        max_length=20,
        choices=ResponseType.choices,
        default=ResponseType.SHORT_TEXT,
    )
    is_mandatory = models.BooleanField(_("Obrigatório"), default=True)
    order = models.PositiveIntegerField(_("Ordem"), default=0)

    class Meta:
        ordering = ("section", "order", "id")
        verbose_name = _("Item de Checklist")
        verbose_name_plural = _("Itens de Checklist")

    def __str__(self):
        return self.label


class ItemOption(AuditableModel):
    item = models.ForeignKey(
        ChecklistItem,
        verbose_name=_("Item"),
        related_name="options",
        on_delete=models.CASCADE,
    )
    text = models.CharField(_("Texto da Opção"), max_length=255)
    order = models.PositiveIntegerField(_("Ordem"), default=0)

    class Meta:
        ordering = ("item", "order", "id")
        verbose_name = _("Opção de Item")
        verbose_name_plural = _("Opções de Item")

    def __str__(self):
        return f"{self.item.label} :: {self.text}"


class ChecklistInstance(AuditableModel):
    """Aplicação de um ChecklistTemplate a uma entidade qualquer do projeto."""

    template = models.ForeignKey(
        ChecklistTemplate,
        verbose_name=_("Template"),
        related_name="instances",
        on_delete=models.CASCADE,
    )

    # Elo Genérico: desacopla este app de Organization/Project/User etc.
    content_type = models.ForeignKey(
        ContentType, verbose_name=_("Tipo de Conteúdo"), on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(_("ID do Objeto"))
    content_object = GenericForeignKey("content_type", "object_id")

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=InstanceStatus.choices,
        default=InstanceStatus.IN_PROGRESS,
    )
    submitted_at = models.DateTimeField(_("Enviado em"), null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("content_type", "object_id"))]
        verbose_name = _("Instância de Checklist")
        verbose_name_plural = _("Instâncias de Checklist")

    def __str__(self):
        return f"{self.template.title} -> {self.content_object} [{self.get_status_display()}]"


class ChecklistItemResponse(AuditableModel):
    instance = models.ForeignKey(
        ChecklistInstance,
        verbose_name=_("Instância"),
        related_name="responses",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        ChecklistItem,
        verbose_name=_("Item"),
        related_name="responses",
        on_delete=models.CASCADE,
    )

    text_value = models.TextField(_("Resposta em Texto"), blank=True, default="")
    boolean_value = models.BooleanField(_("Resposta Booleana"), null=True, blank=True)
    date_value = models.DateField(_("Resposta em Data"), null=True, blank=True)
    selected_options = models.ManyToManyField(
        ItemOption,
        verbose_name=_("Opções Selecionadas"),
        related_name="responses",
        blank=True,
    )

    validation_status = models.CharField(
        _("Status de Validação"),
        max_length=20,
        choices=ResponseValidationStatus.choices,
        default=ResponseValidationStatus.PENDING,
    )
    validation_notes = models.TextField(
        _("Observações do Analista"), blank=True, default=""
    )
    validated_at = models.DateTimeField(_("Validado em"), null=True, blank=True)

    class Meta:
        ordering = ("instance", "item__order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("instance", "item"), name="unique_response_per_item_instance"
            )
        ]
        verbose_name = _("Resposta de Item")
        verbose_name_plural = _("Respostas de Item")

    def __str__(self):
        return f"{self.instance} :: {self.item.label}"


class ChecklistItemAttachment(AuditableModel):
    response = models.ForeignKey(
        ChecklistItemResponse,
        verbose_name=_("Resposta"),
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(_("Arquivo"), upload_to="checklist/attachments/%Y/%m/")
    description = models.CharField(
        _("Descrição"), max_length=255, blank=True, default=""
    )
    uploaded_at = models.DateTimeField(_("Enviado em"), auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at", "-id")
        verbose_name = _("Anexo de Item")
        verbose_name_plural = _("Anexos de Item")

    def __str__(self):
        return f"{self.response} :: {self.file.name}"
