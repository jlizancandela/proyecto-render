import re
import sqlite3
import os

input_sql_path = '/home/jorge/Documentos/proyectos/proyecto-render/docker-init.sql'
output_sql_path = '/home/jorge/Documentos/proyectos/proyecto-render/database/init.sqlite.sql'
output_db_path = '/home/jorge/Documentos/proyectos/proyecto-render/database/database.sqlite'

with open(input_sql_path, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Pattern for INSERT statements
insert_matches = re.findall(r'(INSERT INTO\s+`?\w+`?[^;]+;)', sql_content, re.DOTALL)

table_defs = """-- SQLite schema for Sistema de Reservas
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS `RESERVA`;
DROP TABLE IF EXISTS `HORARIO_ESPECIALISTA`;
DROP TABLE IF EXISTS `ESPECIALISTA_SERVICIO`;
DROP TABLE IF EXISTS `ESPECIALISTA`;
DROP TABLE IF EXISTS `SERVICIO`;
DROP TABLE IF EXISTS `USUARIO`;

CREATE TABLE `USUARIO` (
  `id_usuario` INTEGER PRIMARY KEY AUTOINCREMENT,
  `rol` TEXT CHECK(`rol` IN ('Admin','Especialista','Cliente')) NOT NULL,
  `nombre` TEXT NOT NULL,
  `apellidos` TEXT NOT NULL,
  `email` TEXT NOT NULL UNIQUE,
  `telefono` TEXT DEFAULT NULL,
  `password_hash` TEXT NOT NULL,
  `fecha_registro` TEXT NOT NULL,
  `activo` INTEGER DEFAULT 1,
  `reset_token` TEXT DEFAULT NULL,
  `reset_expiration` TEXT DEFAULT NULL
);

CREATE TABLE `SERVICIO` (
  `id_servicio` INTEGER PRIMARY KEY AUTOINCREMENT,
  `nombre_servicio` TEXT NOT NULL,
  `duracion_minutos` INTEGER NOT NULL,
  `precio` REAL NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `activo` INTEGER DEFAULT 1
);

CREATE TABLE `ESPECIALISTA` (
  `id_especialista` INTEGER PRIMARY KEY AUTOINCREMENT,
  `id_usuario` INTEGER NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `foto_url` TEXT DEFAULT NULL,
  FOREIGN KEY (`id_usuario`) REFERENCES `USUARIO` (`id_usuario`) ON DELETE CASCADE
);
CREATE INDEX `idx_especialista_usuario` ON `ESPECIALISTA` (`id_usuario`);

CREATE TABLE `ESPECIALISTA_SERVICIO` (
  `id_especialista` INTEGER NOT NULL,
  `id_servicio` INTEGER NOT NULL,
  PRIMARY KEY (`id_especialista`,`id_servicio`),
  FOREIGN KEY (`id_especialista`) REFERENCES `ESPECIALISTA` (`id_especialista`) ON DELETE CASCADE,
  FOREIGN KEY (`id_servicio`) REFERENCES `SERVICIO` (`id_servicio`) ON DELETE CASCADE
);
CREATE INDEX `idx_esp_serv_servicio` ON `ESPECIALISTA_SERVICIO` (`id_servicio`);

CREATE TABLE `HORARIO_ESPECIALISTA` (
  `id_horario` INTEGER PRIMARY KEY AUTOINCREMENT,
  `id_especialista` INTEGER NOT NULL,
  `dia_semana` INTEGER NOT NULL,
  `hora_inicio` TEXT NOT NULL,
  `hora_fin` TEXT NOT NULL,
  FOREIGN KEY (`id_especialista`) REFERENCES `ESPECIALISTA` (`id_especialista`) ON DELETE CASCADE
);
CREATE INDEX `idx_horario_especialista` ON `HORARIO_ESPECIALISTA` (`id_especialista`);

CREATE TABLE `RESERVA` (
  `id_reserva` INTEGER PRIMARY KEY AUTOINCREMENT,
  `id_cliente` INTEGER NOT NULL,
  `id_especialista` INTEGER NOT NULL,
  `id_servicio` INTEGER NOT NULL,
  `fecha_reserva` TEXT NOT NULL,
  `hora_inicio` TEXT NOT NULL,
  `hora_fin` TEXT NOT NULL,
  `estado` TEXT DEFAULT 'Pendiente',
  `observaciones` TEXT DEFAULT NULL,
  `fecha_creacion` TEXT DEFAULT (datetime('now', 'localtime')),
  FOREIGN KEY (`id_cliente`) REFERENCES `USUARIO` (`id_usuario`) ON DELETE CASCADE,
  FOREIGN KEY (`id_especialista`) REFERENCES `ESPECIALISTA` (`id_especialista`) ON DELETE CASCADE,
  FOREIGN KEY (`id_servicio`) REFERENCES `SERVICIO` (`id_servicio`) ON DELETE CASCADE
);
CREATE INDEX `idx_reserva_cliente` ON `RESERVA` (`id_cliente`);
CREATE INDEX `idx_reserva_especialista` ON `RESERVA` (`id_especialista`);
CREATE INDEX `idx_reserva_servicio` ON `RESERVA` (`id_servicio`);
"""

# Group inserts by table to maintain FK insertion order:
# USUARIO -> SERVICIO -> ESPECIALISTA -> ESPECIALISTA_SERVICIO -> HORARIO_ESPECIALISTA -> RESERVA
order = ['USUARIO', 'SERVICIO', 'ESPECIALISTA', 'ESPECIALISTA_SERVICIO', 'HORARIO_ESPECIALISTA', 'RESERVA']
inserts_by_table = {tbl: [] for tbl in order}

for stmt in insert_matches:
    match = re.search(r'INSERT INTO\s+`?(\w+)`?', stmt)
    if match:
        tbl = match.group(1)
        if tbl in inserts_by_table:
            inserts_by_table[tbl].append(stmt)
        else:
            print(f"Unknown table for insert: {tbl}")

ordered_inserts = []
for tbl in order:
    ordered_inserts.extend(inserts_by_table[tbl])

final_sql = table_defs + "\n\nBEGIN TRANSACTION;\n" + "\n".join(ordered_inserts) + "\nCOMMIT;\n\nPRAGMA foreign_keys = ON;\n"

with open(output_sql_path, 'w', encoding='utf-8') as f:
    f.write(final_sql)

print(f"Wrote {output_sql_path}")

# Now test executing it into SQLite database
if os.path.exists(output_db_path):
    os.remove(output_db_path)

conn = sqlite3.connect(output_db_path)
conn.executescript(final_sql)

# Verify counts
cursor = conn.cursor()
for tbl in order:
    cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`")
    count = cursor.fetchone()[0]
    print(f"Table {tbl}: {count} rows")

# Check FK integrity
cursor.execute("PRAGMA foreign_key_check;")
errors = cursor.fetchall()
if errors:
    print(f"Foreign key check errors: {errors}")
else:
    print("Foreign key check passed with 0 errors!")

conn.close()
