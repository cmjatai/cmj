


ALTER TABLE ONLY public.compilacao_dispositivo DROP CONSTRAINT "D3c6d5621f48fa7e5b6d06891fb02b28";
ALTER TABLE ONLY public.compilacao_dispositivo DROP CONSTRAINT "D841742854a366eaaec81988f653b0e2";
ALTER TABLE ONLY public.compilacao_dispositivo DROP CONSTRAINT af53650d5bb9e9b4d10b9b707a357623;
ALTER TABLE ONLY public.compilacao_dispositivo DROP CONSTRAINT co_dispositivo_vigencia_id_63a750b_fk_compilacao_dispositivo_id;
ALTER TABLE ONLY public.compilacao_dispositivo DROP CONSTRAINT compila_dispositivo_pai_id_2317701_fk_compilacao_dispositivo_id;

ALTER TABLE ONLY public.compilacao_dispositivo
    ADD CONSTRAINT "D3c6d5621f48fa7e5b6d06891fb02b28" FOREIGN KEY (dispositivo_subsequente_id) REFERENCES public.compilacao_dispositivo(id) DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE ONLY public.compilacao_dispositivo
    ADD CONSTRAINT "D841742854a366eaaec81988f653b0e2" FOREIGN KEY (dispositivo_substituido_id) REFERENCES public.compilacao_dispositivo(id) DEFERRABLE INITIALLY DEFERRED;



ALTER TABLE ONLY public.compilacao_dispositivo
    ADD CONSTRAINT af53650d5bb9e9b4d10b9b707a357623 FOREIGN KEY (dispositivo_atualizador_id) REFERENCES public.compilacao_dispositivo(id) DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE ONLY public.compilacao_dispositivo
    ADD CONSTRAINT co_dispositivo_vigencia_id_63a750b_fk_compilacao_dispositivo_id FOREIGN KEY (dispositivo_vigencia_id) REFERENCES public.compilacao_dispositivo(id) DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE ONLY public.compilacao_dispositivo
    ADD CONSTRAINT compila_dispositivo_pai_id_2317701_fk_compilacao_dispositivo_id FOREIGN KEY (dispositivo_pai_id) REFERENCES public.compilacao_dispositivo(id) DEFERRABLE INITIALLY DEFERRED;

