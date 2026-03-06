CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 96ee93975f8a

INSERT INTO alembic_version (version_num) VALUES ('96ee93975f8a') RETURNING version_num;

-- Running upgrade 96ee93975f8a -> a69c80be508b

CREATE TABLE ppx_storage_var (
    id INTEGER NOT NULL, 
    "key" VARCHAR NOT NULL, 
    val VARCHAR DEFAULT '' NOT NULL, 
    remark VARCHAR DEFAULT '' NOT NULL, 
    created_at DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'localtime')), 
    updated_at DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'localtime')), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_ppx_storage_var_key ON ppx_storage_var ("key");

UPDATE alembic_version SET version_num='a69c80be508b' WHERE alembic_version.version_num = '96ee93975f8a';

-- Running upgrade a69c80be508b -> 802ec4ff5306

DROP INDEX ix_ppx_storage_var_key;

CREATE UNIQUE INDEX ix_ppx_storage_var_key ON ppx_storage_var ("key");

UPDATE alembic_version SET version_num='802ec4ff5306' WHERE alembic_version.version_num = 'a69c80be508b';

-- Running upgrade 802ec4ff5306 -> 5906e4bc71c2

ALTER TABLE ppx_storage_var ADD COLUMN sku VARCHAR NOT NULL;

ALTER TABLE ppx_storage_var ADD COLUMN price NUMERIC(10, 2) DEFAULT '0.00' NOT NULL;

ALTER TABLE ppx_storage_var ADD COLUMN star NUMERIC(10, 2) DEFAULT '0.00' NOT NULL;

ALTER TABLE ppx_storage_var ADD COLUMN status INTEGER DEFAULT '0' NOT NULL;

DROP INDEX ix_ppx_storage_var_key;

CREATE UNIQUE INDEX ix_ppx_storage_var_sku ON ppx_storage_var (sku);

ALTER TABLE ppx_storage_var DROP COLUMN remark;

ALTER TABLE ppx_storage_var DROP COLUMN val;

ALTER TABLE ppx_storage_var DROP COLUMN "key";

UPDATE alembic_version SET version_num='5906e4bc71c2' WHERE alembic_version.version_num = '802ec4ff5306';

-- Running upgrade 5906e4bc71c2 -> 6c5c671a37cc

UPDATE alembic_version SET version_num='6c5c671a37cc' WHERE alembic_version.version_num = '5906e4bc71c2';

-- Running upgrade 6c5c671a37cc -> 88b0c291da2e

UPDATE alembic_version SET version_num='88b0c291da2e' WHERE alembic_version.version_num = '6c5c671a37cc';

-- Running upgrade 88b0c291da2e -> 259855d03638

CREATE TABLE ppx_config_var (
    "key" VARCHAR NOT NULL, 
    value VARCHAR NOT NULL, 
    id INTEGER NOT NULL, 
    created_at DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'localtime')), 
    updated_at DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'localtime')), 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_ppx_config_var_key ON ppx_config_var ("key");

UPDATE alembic_version SET version_num='259855d03638' WHERE alembic_version.version_num = '88b0c291da2e';

-- Running upgrade 259855d03638 -> 21115bc93eda

UPDATE alembic_version SET version_num='21115bc93eda' WHERE alembic_version.version_num = '259855d03638';

-- Running upgrade 21115bc93eda -> b14d43f063f4

UPDATE alembic_version SET version_num='b14d43f063f4' WHERE alembic_version.version_num = '21115bc93eda';

-- Running upgrade b14d43f063f4 -> e18815479f93

UPDATE alembic_version SET version_num='e18815479f93' WHERE alembic_version.version_num = 'b14d43f063f4';

