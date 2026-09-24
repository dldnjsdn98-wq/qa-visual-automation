BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_bootstrap

INSERT INTO alembic_version (version_num) VALUES ('0001_bootstrap') RETURNING alembic_version.version_num;

-- Running upgrade 0001_bootstrap -> 0002_phase1_domain

CREATE TABLE projects (
    slug VARCHAR(64) NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    description TEXT, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (slug)
);

CREATE TABLE builds (
    label VARCHAR(120) NOT NULL, 
    description TEXT, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, id), 
    UNIQUE (project_id, label)
);

CREATE INDEX ix_builds_project_id ON builds (project_id);

CREATE TABLE categories (
    slug VARCHAR(64) NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, id), 
    UNIQUE (project_id, slug)
);

CREATE INDEX ix_categories_project_id ON categories (project_id);

CREATE TABLE locales (
    code VARCHAR(63) NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, code), 
    UNIQUE (project_id, id)
);

CREATE INDEX ix_locales_project_id ON locales (project_id);

CREATE TABLE string_keys (
    string_id VARCHAR(128) NOT NULL, 
    description TEXT, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, id), 
    UNIQUE (project_id, string_id)
);

CREATE INDEX ix_string_keys_project_id ON string_keys (project_id);

CREATE TABLE situations (
    category_id UUID NOT NULL, 
    slug VARCHAR(64) NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    description TEXT, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id, category_id) REFERENCES categories (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, category_id, id), 
    UNIQUE (project_id, category_id, slug), 
    UNIQUE (project_id, id)
);

CREATE INDEX ix_situations_project_id ON situations (project_id);

CREATE TABLE string_entries (
    build_id UUID NOT NULL, 
    locale_id UUID NOT NULL, 
    string_key_id UUID NOT NULL, 
    text TEXT NOT NULL, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_entry_text_length CHECK (char_length(text) <= 10000), 
    FOREIGN KEY(project_id, build_id) REFERENCES builds (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id, locale_id) REFERENCES locales (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id, string_key_id) REFERENCES string_keys (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, build_id, string_key_id, locale_id)
);

CREATE INDEX ix_entries_catalog ON string_entries (project_id, build_id, locale_id, string_key_id);

CREATE INDEX ix_entries_key ON string_entries (project_id, string_key_id);

CREATE INDEX ix_entries_locale ON string_entries (project_id, locale_id);

CREATE INDEX ix_string_entries_project_id ON string_entries (project_id);

CREATE TABLE screenshots (
    build_id UUID NOT NULL, 
    locale_id UUID NOT NULL, 
    category_id UUID NOT NULL, 
    situation_id UUID NOT NULL, 
    source VARCHAR(32) NOT NULL, 
    original_filename VARCHAR(255) NOT NULL, 
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    storage_key TEXT NOT NULL, 
    file_hash CHAR(64) NOT NULL, 
    media_type VARCHAR(32) NOT NULL, 
    size_bytes BIGINT NOT NULL, 
    width INTEGER NOT NULL, 
    height INTEGER NOT NULL, 
    metadata_version INTEGER DEFAULT '1' NOT NULL, 
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL, 
    client_upload_id UUID, 
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    project_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_screenshot_hash CHECK (file_hash ~ '^[0-9a-f]{64}$'), 
    CONSTRAINT ck_screenshot_metadata CHECK (metadata_version = 1 AND jsonb_typeof(metadata) = 'object'), 
    CONSTRAINT ck_screenshot_phase1 CHECK (source = 'manual' AND client_upload_id IS NULL), 
    CONSTRAINT ck_screenshot_positive CHECK (size_bytes > 0 AND width > 0 AND height > 0), 
    FOREIGN KEY(project_id, build_id) REFERENCES builds (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id, category_id, situation_id) REFERENCES situations (project_id, category_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id, locale_id) REFERENCES locales (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, id), 
    UNIQUE (storage_key)
);

CREATE INDEX ix_screenshots_category ON screenshots (project_id, category_id);

CREATE INDEX ix_screenshots_filters ON screenshots (project_id, build_id, locale_id, situation_id, uploaded_at DESC, id DESC);

CREATE INDEX ix_screenshots_locale ON screenshots (project_id, locale_id);

CREATE INDEX ix_screenshots_project_id ON screenshots (project_id);

CREATE INDEX ix_screenshots_recent ON screenshots (project_id, uploaded_at DESC, id DESC);

CREATE INDEX ix_screenshots_situation ON screenshots (project_id, situation_id);

CREATE TABLE situation_expected_strings (
    project_id UUID NOT NULL, 
    build_id UUID NOT NULL, 
    situation_id UUID NOT NULL, 
    string_key_id UUID NOT NULL, 
    position INTEGER NOT NULL, 
    PRIMARY KEY (project_id, build_id, situation_id, string_key_id), 
    CONSTRAINT ck_expected_position CHECK (position >= 0), 
    FOREIGN KEY(project_id, build_id) REFERENCES builds (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id, situation_id) REFERENCES situations (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id, string_key_id) REFERENCES string_keys (project_id, id) ON DELETE RESTRICT, 
    FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT, 
    UNIQUE (project_id, build_id, situation_id, position)
);

CREATE INDEX ix_expected_key ON situation_expected_strings (project_id, string_key_id);

CREATE INDEX ix_expected_situation ON situation_expected_strings (project_id, situation_id);

CREATE INDEX ix_situation_expected_strings_project_id ON situation_expected_strings (project_id);

UPDATE alembic_version SET version_num='0002_phase1_domain' WHERE alembic_version.version_num = '0001_bootstrap';

COMMIT;

