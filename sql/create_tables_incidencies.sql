
-- Crear taula incidències correlacions amb les capes
CREATE TABLE if not exists cicle_aigua.incidencies_correlacions
(
    nom_capa text,
    id_capa integer,
    id_incidencia integer,
    CONSTRAINT incidencies_correlacions_pkey PRIMARY KEY (id_capa, id_incidencia)
);

-- crear taula d'incidències
CREATE TABLE if not exists cicle_aigua.incidencies
(
    id serial,
    data_inici date,
    usuari text,
    descripcio text,
    estat text,
    CONSTRAINT incidencies_pkey PRIMARY KEY (id)
);
   
-- Fem la taula de fotos
CREATE TABLE if not exists cicle_aigua.incidencies_fotos
(
    id serial,
    id_incidencia integer,
    link_foto text,
    observacions text,
    CONSTRAINT incidencies_fotos_pkey PRIMARY KEY (id)
);


-- Fí
