from django.db import connections


def sql(s, db='legacy_portal'):
    print (s)
    cursor = connections[db].cursor()
    cursor.execute(s)
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


if __name__ == '__main__':
    #pre migração... limpeza das constaints... a migração de fato é feita
    #    pelo sislegis na aplicação java.
    #após a migração, executar o arquivo sql:
    #    executar_depois_de_exportar_sislegis.sql para recriar as constaints.
    r = sql('''
        SELECT * FROM information_schema.table_constraints
            where table_name = 'compilacao_dispositivo' and
                  constraint_type = 'FOREIGN KEY'
        ''', 'default')

    for i in r:
        try:
            sql('''
                ALTER TABLE ONLY compilacao_dispositivo
                    DROP CONSTRAINT "{}"
            '''.format(i['constraint_name']), 'default')
        except:
            try:
                sql('''
                    ALTER TABLE ONLY compilacao_dispositivo
                        DROP CONSTRAINT {}
                '''.format(i['constraint_name']), 'default')
            except:
                pass
