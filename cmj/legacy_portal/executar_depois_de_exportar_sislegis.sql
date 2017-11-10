ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT compilacao_d_publicacao_id_4d8f932d_fk_compilacao_publicacao_id FOREIGN KEY (publicacao_id)
      REFERENCES public.compilacao_publicacao (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

INSERT INTO compilacao_tipodispositivo (id, nome, class_css, rotulo_prefixo_html, rotulo_prefixo_texto, rotulo_ordinal, rotulo_sufixo_texto, rotulo_sufixo_html, texto_prefixo_html, texto_sufixo_html, nota_automatica_prefixo_html, nota_automatica_sufixo_html, contagem_continua, formato_variacao0, formato_variacao1, formato_variacao2, formato_variacao3, formato_variacao4, formato_variacao5, rotulo_separador_variacao01, rotulo_separador_variacao12, rotulo_separador_variacao23, rotulo_separador_variacao34, rotulo_separador_variacao45, dispositivo_de_articulacao, dispositivo_de_alteracao) 
   VALUES (118, 'Item de Sessão', 'itemsecao', '', 'Item de Sessão ', 0, '', '<br>', '', '<br>', '<br>', '', false, 'I', '1', '1', '1', '1', '1', '-', '-', '-', '-', '-', false, false);

INSERT INTO compilacao_tipodispositivorelationship (filho_permitido_id, pai_id, filho_de_insercao_automatica, perfil_id, quantidade_permitida, permitir_variacao) VALUES (118, 116, false, 1, -1, false);
INSERT INTO compilacao_tipodispositivorelationship (filho_permitido_id, pai_id, filho_de_insercao_automatica, perfil_id, quantidade_permitida, permitir_variacao) VALUES (118, 117, false, 1, -1, false);
INSERT INTO compilacao_tipodispositivorelationship (filho_permitido_id, pai_id, filho_de_insercao_automatica, perfil_id, quantidade_permitida, permitir_variacao) VALUES (119, 118, false, 1, -1, false);

INSERT INTO compilacao_tipodispositivorelationship (filho_permitido_id, pai_id, filho_de_insercao_automatica, perfil_id, quantidade_permitida, permitir_variacao) VALUES (118, 116, false, 2, -1, true);
INSERT INTO compilacao_tipodispositivorelationship (filho_permitido_id, pai_id, filho_de_insercao_automatica, perfil_id, quantidade_permitida, permitir_variacao) VALUES (118, 117, false, 2, -1, true);
INSERT INTO compilacao_tipodispositivorelationship (filho_permitido_id, pai_id, filho_de_insercao_automatica, perfil_id, quantidade_permitida, permitir_variacao) VALUES (119, 118, false, 2, -1, true);


ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT c_tipo_dispositivo_id_442b890e_fk_compilacao_tipodispositivo_id FOREIGN KEY (tipo_dispositivo_id)
      REFERENCES public.compilacao_tipodispositivo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT compilacao_disp_ta_id_03c79b52_fk_compilacao_textoarticulado_id FOREIGN KEY (ta_id)
      REFERENCES public.compilacao_textoarticulado (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT compi_ta_publicado_id_5f99413e_fk_compilacao_textoarticulado_id FOREIGN KEY (ta_publicado_id)
      REFERENCES public.compilacao_textoarticulado (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;



ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT compila_dispositivo_pai_id_2317701_fk_compilacao_dispositivo_id FOREIGN KEY (dispositivo_pai_id)
      REFERENCES public.compilacao_dispositivo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT co_dispositivo_vigencia_id_63a750b_fk_compilacao_dispositivo_id FOREIGN KEY (dispositivo_vigencia_id)
      REFERENCES public.compilacao_dispositivo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT af53650d5bb9e9b4d10b9b707a357623 FOREIGN KEY (dispositivo_atualizador_id)
      REFERENCES public.compilacao_dispositivo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT "D3c6d5621f48fa7e5b6d06891fb02b28" FOREIGN KEY (dispositivo_subsequente_id)
      REFERENCES public.compilacao_dispositivo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.compilacao_dispositivo
  ADD CONSTRAINT "D841742854a366eaaec81988f653b0e2" FOREIGN KEY (dispositivo_substituido_id)
      REFERENCES public.compilacao_dispositivo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;
