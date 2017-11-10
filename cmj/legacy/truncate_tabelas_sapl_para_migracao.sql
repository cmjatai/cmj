
ALTER TABLE public.sigad_classe DROP COLUMN parlamentar_id;
ALTER TABLE public.sigad_documento_parlamentares DROP COLUMN parlamentar_id;
ALTER TABLE public.cerimonial_filiacaopartidaria DROP COLUMN partido_id;
ALTER TABLE public.sigad_documento_materias DROP COLUMN materialegislativa_id;


TRUNCATE
"materia_assuntomateria",
"reversion_version", 
"protocoloadm_documentoacessorioadministrativo", 
"base_autor", 
"parlamentares_tipoafastamento", 
"comissoes_comissao", 
"compilacao_tipovide", 
"parlamentares_composicaocoligacao", 
"sessao_sessaoplenaria", 
"parlamentares_parlamentar", 
"sessao_oradorexpediente", 
"parlamentares_nivelinstrucao", 
"painel_painel", 
"compilacao_perfilestruturaltextoarticulado", 
"norma_normajuridica_assuntos", 
"sessao_votoparlamentar", 
"parlamentares_mandato", 
"protocoloadm_documentoadministrativo", 
"compilacao_publicacao", 
"norma_normajuridica", 
"materia_despachoinicial", 
"parlamentares_composicaomesa", 
"comissoes_composicao", 
"easy_thumbnails_thumbnaildimensions", 
"sessao_cargobancada", 
"easy_thumbnails_source", 
"compilacao_nota", 
"parlamentares_situacaomilitar", 
"materia_tipodocumento", 
"base_casalegislativa", 
"parlamentares_municipio", 
"parlamentares_filiacao", 
"sessao_tiposessaoplenaria", 
"sessao_tiporesultadovotacao", 
"parlamentares_partido", 
"materia_materiaassunto", 
"parlamentares_frente", 
"protocoloadm_statustramitacaoadministrativo", 
"comissoes_tipocomissao",
"parlamentares_coligacao", 
"parlamentares_frente_parlamentares", 

"parlamentares_legislatura", 
"materia_relatoria", 
"materia_regimetramitacao", 
"materia_tipoproposicao", 
"base_constraint", 
"materia_tramitacao", 
"sessao_integrantemesa", 
"compilacao_textoarticulado_owners", 
"sessao_ordemdia", 
"sessao_bloco", 
"lexml_lexmlprovedor", 
"compilacao_tiponota", 
"parlamentares_votante", 
"comissoes_participacao", 
"sessao_expedientesessao", 
"lexml_lexmlpublicador", 
"norma_tiponormajuridica", 
"painel_cronometro", 
"norma_legislacaocitada", 
"norma_tipovinculonormajuridica", 
"materia_materialegislativa", 
"comissoes_periodo", 
"compilacao_tipopublicacao", 
"parlamentares_sessaolegislativa", 
"easy_thumbnails_thumbnail", 
"base_tipoautor", 
"materia_orgao", 
"materia_unidadetramitacao", 
"sessao_bancada", 
"compilacao_tipotextoarticulado_perfis", 
"parlamentares_tipodependente", 
"sessao_registrovotacao", 
"compilacao_tipotextoarticulado", 
"parlamentares_cargomesa", 
"materia_anexada", 
"sessao_orador", 
"materia_statustramitacao", 
"compilacao_textoarticulado", 
"materia_proposicao", 
"sessao_tipoexpediente", 
"materia_autoria", 
"base_argumento", 
"base_appconfig", 
"materia_acompanhamentomateria", 
"base_problemamigracao", 
"materia_tipofimrelatoria", 
"comissoes_cargocomissao", 
"protocoloadm_tipodocumentoadministrativo", 
"sessao_bloco_partidos", 
"sessao_expedientemateria", 
"compilacao_tipodispositivorelationship", 
"sessao_resumoordenacao", 
"protocoloadm_tramitacaoadministrativo", 
"compilacao_vide", 
"materia_tipoproposicao_perfis", 
"parlamentares_dependente", 
"sessao_sessaoplenariapresenca", 
"materia_documentoacessorio", 
"materia_parecer", 
"compilacao_dispositivo", 
"compilacao_tipodispositivo", 
"compilacao_veiculopublicacao", 
"sessao_presencaordemdia", 
"norma_normarelacionada", 
"materia_numeracao", 
"protocoloadm_protocolo", 
"reversion_revision", 
"materia_origem", 
"materia_tipomaterialegislativa", 
"norma_assuntonorma";
SELECT setval(pg_get_serial_sequence('"easy_thumbnails_source"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"easy_thumbnails_thumbnail"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"easy_thumbnails_thumbnaildimensions"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"reversion_revision"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"reversion_version"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_casalegislativa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_problemamigracao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_constraint"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_argumento"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_appconfig"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_tipoautor"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"base_autor"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_legislatura"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_sessaolegislativa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_coligacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_partido"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_composicaocoligacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_municipio"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_nivelinstrucao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_situacaomilitar"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_parlamentar"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_tipodependente"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_dependente"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_filiacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_tipoafastamento"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_mandato"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_cargomesa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_composicaomesa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_frente"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"parlamentares_votante"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"comissoes_tipocomissao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"comissoes_comissao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"comissoes_periodo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"comissoes_cargocomissao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"comissoes_composicao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"comissoes_participacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_tipoproposicao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_tipomaterialegislativa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_regimetramitacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_origem"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_materialegislativa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_autoria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_acompanhamentomateria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_anexada"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_assuntomateria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_despachoinicial"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_tipodocumento"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_documentoacessorio"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_materiaassunto"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_numeracao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_orgao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_tipofimrelatoria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_relatoria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_parecer"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_proposicao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_statustramitacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_unidadetramitacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"materia_tramitacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"norma_assuntonorma"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"norma_tiponormajuridica"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"norma_normajuridica"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"norma_legislacaocitada"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"norma_tipovinculonormajuridica"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"norma_normarelacionada"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_cargobancada"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_bancada"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_tiposessaoplenaria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_sessaoplenaria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_expedientemateria"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_tipoexpediente"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_expedientesessao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_integrantemesa"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_orador"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_oradorexpediente"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_ordemdia"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_presencaordemdia"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_tiporesultadovotacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_registrovotacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_votoparlamentar"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_sessaoplenariapresenca"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_bloco"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"sessao_resumoordenacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"lexml_lexmlprovedor"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"lexml_lexmlpublicador"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"painel_painel"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"painel_cronometro"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"protocoloadm_tipodocumentoadministrativo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"protocoloadm_protocolo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"protocoloadm_documentoadministrativo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"protocoloadm_documentoacessorioadministrativo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"protocoloadm_statustramitacaoadministrativo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"protocoloadm_tramitacaoadministrativo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_perfilestruturaltextoarticulado"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_tipotextoarticulado"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_textoarticulado"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_tiponota"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_tipovide"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_tipodispositivo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_tipodispositivorelationship"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_tipopublicacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_veiculopublicacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_publicacao"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_dispositivo"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_vide"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"compilacao_nota"','id'), 1, false);

ALTER TABLE public.sigad_classe ADD COLUMN parlamentar_id integer;
ALTER TABLE public.sigad_documento_parlamentares ADD COLUMN parlamentar_id integer;
ALTER TABLE public.sigad_documento_parlamentares ALTER COLUMN parlamentar_id SET NOT NULL;
ALTER TABLE public.cerimonial_filiacaopartidaria ADD COLUMN partido_id integer;
ALTER TABLE public.cerimonial_filiacaopartidaria ALTER COLUMN partido_id SET NOT NULL;
ALTER TABLE public.sigad_documento_materias ADD COLUMN materialegislativa_id integer;
ALTER TABLE public.sigad_documento_materias ALTER COLUMN materialegislativa_id SET NOT NULL;


ALTER TABLE public.sigad_classe
  ADD CONSTRAINT sigad_c_parlamentar_id_57900a51_fk_parlamentares_parlamentar_id FOREIGN KEY (parlamentar_id)
      REFERENCES public.parlamentares_parlamentar (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.sigad_documento_parlamentares
  ADD CONSTRAINT sigad_d_parlamentar_id_73882b15_fk_parlamentares_parlamentar_id FOREIGN KEY (parlamentar_id)
      REFERENCES public.parlamentares_parlamentar (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.cerimonial_filiacaopartidaria
  ADD CONSTRAINT cerimonial_fili_partido_id_6fbd36b2_fk_parlamentares_partido_id FOREIGN KEY (partido_id)
      REFERENCES public.parlamentares_partido (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.sigad_documento_materias
  ADD CONSTRAINT "D9b98424f881dd0322f239736467ba95" FOREIGN KEY (materialegislativa_id)
      REFERENCES public.materia_materialegislativa (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;





