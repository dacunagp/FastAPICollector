CREATE TABLE IF NOT EXISTS observaciones_predefinidas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    texto VARCHAR(255) NOT NULL,
    categoria VARCHAR(50) DEFAULT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO observaciones_predefinidas (texto, categoria) 
SELECT * FROM (SELECT 'Pozo seco', NULL) AS tmp 
WHERE NOT EXISTS (SELECT 1 FROM observaciones_predefinidas LIMIT 1);

INSERT INTO observaciones_predefinidas (texto, categoria) 
SELECT * FROM (SELECT 'Bomba en mantención', NULL) AS tmp 
WHERE NOT EXISTS (SELECT 1 FROM observaciones_predefinidas WHERE texto='Bomba en mantención' LIMIT 1);

INSERT INTO observaciones_predefinidas (texto, categoria) 
SELECT * FROM (SELECT 'Sin acceso al punto', NULL) AS tmp 
WHERE NOT EXISTS (SELECT 1 FROM observaciones_predefinidas WHERE texto='Sin acceso al punto' LIMIT 1);

INSERT INTO observaciones_predefinidas (texto, categoria) 
SELECT * FROM (SELECT 'Muestra con sedimentos', NULL) AS tmp 
WHERE NOT EXISTS (SELECT 1 FROM observaciones_predefinidas WHERE texto='Muestra con sedimentos' LIMIT 1);
