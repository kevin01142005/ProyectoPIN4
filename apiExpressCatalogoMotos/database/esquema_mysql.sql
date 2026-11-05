-- 1.- Tener la base de datos creada
-- Ejecutar este script en phpMyAdmin (XAMPP) antes de iniciar la API con: node index.js
-- (En la base de datos de la nube no se ejecutan las dos primeras líneas: ya existe "defaultdb").

create database if not exists catalogo_motos character set utf8mb4 collate utf8mb4_unicode_ci;
use catalogo_motos;

CREATE TABLE IF NOT EXISTS marcas (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre       VARCHAR(100)    NOT NULL,
  pais_origen  VARCHAR(100)    NULL,
  estado       TINYINT(1)      NOT NULL DEFAULT 1,
  creado       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_marcas_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS modelos (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  marca_id     BIGINT UNSIGNED NOT NULL,
  nombre       VARCHAR(100)    NOT NULL,
  tipo         VARCHAR(50)     NULL,
  estado       TINYINT(1)      NOT NULL DEFAULT 1,
  creado       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_modelos_marca_nombre (marca_id, nombre),
  CONSTRAINT fk_modelos_marca FOREIGN KEY (marca_id) REFERENCES marcas (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS versiones (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  modelo_id    BIGINT UNSIGNED NOT NULL,
  anio         SMALLINT UNSIGNED NOT NULL,
  cilindraje   SMALLINT UNSIGNED NOT NULL,
  estado       TINYINT(1)      NOT NULL DEFAULT 1,
  creado       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_versiones_modelo_anio_cc (modelo_id, anio, cilindraje),
  CONSTRAINT fk_versiones_modelo FOREIGN KEY (modelo_id) REFERENCES modelos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Datos de ejemplo (insert ignore: si ya existen no se duplican)

insert ignore into marcas(nombre, pais_origen) values
  ('Yamaha', 'Japón'),
  ('Honda', 'Japón'),
  ('Suzuki', 'Japón'),
  ('Kawasaki', 'Japón'),
  ('Bajaj', 'India'),
  ('TVS', 'India'),
  ('AKT', 'Colombia'),
  ('KTM', 'Austria');

insert ignore into modelos(marca_id, nombre, tipo) select id, 'FZ 150', 'Naked' from marcas where nombre = 'Yamaha';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'XTZ 125', 'Enduro' from marcas where nombre = 'Yamaha';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'NMAX 155', 'Scooter' from marcas where nombre = 'Yamaha';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'MT-03', 'Naked' from marcas where nombre = 'Yamaha';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'CB 190R', 'Naked' from marcas where nombre = 'Honda';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'XR 150L', 'Enduro' from marcas where nombre = 'Honda';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Wave 110S', 'Semiautomática' from marcas where nombre = 'Honda';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'PCX 160', 'Scooter' from marcas where nombre = 'Honda';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Gixxer 150', 'Deportiva' from marcas where nombre = 'Suzuki';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'GN 125', 'Custom' from marcas where nombre = 'Suzuki';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'DR 650', 'Enduro' from marcas where nombre = 'Suzuki';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Ninja 400', 'Deportiva' from marcas where nombre = 'Kawasaki';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'KLX 230', 'Enduro' from marcas where nombre = 'Kawasaki';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Pulsar NS 200', 'Naked' from marcas where nombre = 'Bajaj';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Boxer CT 100', 'Urbana' from marcas where nombre = 'Bajaj';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Dominar 400', 'Turismo' from marcas where nombre = 'Bajaj';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Apache RTR 160 4V', 'Deportiva' from marcas where nombre = 'TVS';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Raider 125', 'Naked' from marcas where nombre = 'TVS';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'NKD 125', 'Naked' from marcas where nombre = 'AKT';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'TT 180', 'Enduro' from marcas where nombre = 'AKT';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Duke 200', 'Naked' from marcas where nombre = 'KTM';
insert ignore into modelos(marca_id, nombre, tipo) select id, 'Duke 390', 'Naked' from marcas where nombre = 'KTM';

insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2020, 149 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'FZ 150';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 149 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'FZ 150';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 149 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'FZ 150';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2019, 124 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'XTZ 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 124 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'XTZ 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 155 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'NMAX 155';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 155 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'NMAX 155';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 321 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'MT-03';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 321 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Yamaha' and mo.nombre = 'MT-03';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 184 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'CB 190R';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 184 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'CB 190R';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2020, 149 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'XR 150L';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 149 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'XR 150L';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 149 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'XR 150L';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 109 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'Wave 110S';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 157 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'PCX 160';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 157 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Honda' and mo.nombre = 'PCX 160';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 155 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Suzuki' and mo.nombre = 'Gixxer 150';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 155 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Suzuki' and mo.nombre = 'Gixxer 150';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2020, 125 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Suzuki' and mo.nombre = 'GN 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 125 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Suzuki' and mo.nombre = 'GN 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2019, 644 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Suzuki' and mo.nombre = 'DR 650';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 399 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Kawasaki' and mo.nombre = 'Ninja 400';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 399 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Kawasaki' and mo.nombre = 'Ninja 400';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 233 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Kawasaki' and mo.nombre = 'KLX 230';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 233 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Kawasaki' and mo.nombre = 'KLX 230';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2020, 199 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Pulsar NS 200';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 199 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Pulsar NS 200';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 199 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Pulsar NS 200';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 102 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Boxer CT 100';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 102 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Boxer CT 100';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 373 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Dominar 400';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 373 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'Bajaj' and mo.nombre = 'Dominar 400';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 159 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'TVS' and mo.nombre = 'Apache RTR 160 4V';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 159 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'TVS' and mo.nombre = 'Apache RTR 160 4V';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 125 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'TVS' and mo.nombre = 'Raider 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 124 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'AKT' and mo.nombre = 'NKD 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 124 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'AKT' and mo.nombre = 'NKD 125';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 180 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'AKT' and mo.nombre = 'TT 180';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2021, 200 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'KTM' and mo.nombre = 'Duke 200';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2023, 200 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'KTM' and mo.nombre = 'Duke 200';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2022, 373 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'KTM' and mo.nombre = 'Duke 390';
insert ignore into versiones(modelo_id, anio, cilindraje) select mo.id, 2024, 373 from modelos mo join marcas ma on ma.id = mo.marca_id where ma.nombre = 'KTM' and mo.nombre = 'Duke 390';
