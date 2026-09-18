with codigos as (
    select * from (values
        ('11','RO','Rondonia','Norte'), ('12','AC','Acre','Norte'),
        ('13','AM','Amazonas','Norte'), ('14','RR','Roraima','Norte'),
        ('15','PA','Para','Norte'), ('16','AP','Amapa','Norte'),
        ('17','TO','Tocantins','Norte'), ('21','MA','Maranhao','Nordeste'),
        ('22','PI','Piaui','Nordeste'), ('23','CE','Ceara','Nordeste'),
        ('24','RN','Rio Grande do Norte','Nordeste'), ('25','PB','Paraiba','Nordeste'),
        ('26','PE','Pernambuco','Nordeste'), ('27','AL','Alagoas','Nordeste'),
        ('28','SE','Sergipe','Nordeste'), ('29','BA','Bahia','Nordeste'),
        ('31','MG','Minas Gerais','Sudeste'), ('32','ES','Espirito Santo','Sudeste'),
        ('33','RJ','Rio de Janeiro','Sudeste'), ('35','SP','Sao Paulo','Sudeste'),
        ('41','PR','Parana','Sul'), ('42','SC','Santa Catarina','Sul'),
        ('43','RS','Rio Grande do Sul','Sul'), ('50','MS','Mato Grosso do Sul','Centro-Oeste'),
        ('51','MT','Mato Grosso','Centro-Oeste'), ('52','GO','Goias','Centro-Oeste'),
        ('53','DF','Distrito Federal','Centro-Oeste')
    ) as t(uf_codigo, uf, uf_nome, regiao)
)
select * from codigos
