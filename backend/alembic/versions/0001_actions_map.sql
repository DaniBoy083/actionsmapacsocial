CREATE TABLE actions_map.acoes_map_acoes (
	id VARCHAR(36) NOT NULL,
	versao INTEGER NOT NULL,
	nome VARCHAR(160) NOT NULL,
	categoria VARCHAR(80) NOT NULL,
	descricao TEXT NOT NULL,
	resumo_publico TEXT NOT NULL,
	inicio_em VARCHAR(10),
	fim_em VARCHAR(10),
	status VARCHAR(20) NOT NULL,
	locais JSON NOT NULL,
	criado_por VARCHAR(160) NOT NULL,
	aprovado_por VARCHAR(160),
	publicado_por VARCHAR(160),
	criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
	atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE INDEX ix_actions_map_acoes_map_acoes_status ON actions_map.acoes_map_acoes (status);

CREATE TABLE actions_map.acoes_map_auditoria (
	id VARCHAR(36) NOT NULL,
	profissional_id VARCHAR(160) NOT NULL,
	operacao VARCHAR(60) NOT NULL,
	entidade_id VARCHAR(160) NOT NULL,
	criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE actions_map.acoes_map_beneficiarios (
	id VARCHAR(36) NOT NULL,
	dados_cifrados TEXT NOT NULL,
	municipio_residencia_ibge VARCHAR(7),
	PRIMARY KEY (id)
);

CREATE TABLE actions_map.acoes_map_importacoes (
	id VARCHAR(36) NOT NULL,
	hash_arquivo VARCHAR(64) NOT NULL,
	paginas INTEGER NOT NULL,
	autor_id VARCHAR(160) NOT NULL,
	criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE actions_map.acoes_map_integracoes_outbox (
	id VARCHAR(36) NOT NULL,
	idempotency_key VARCHAR(160) NOT NULL,
	payload JSON NOT NULL,
	status VARCHAR(20) NOT NULL,
	tentativas INTEGER NOT NULL,
	proxima_tentativa TIMESTAMP WITH TIME ZONE NOT NULL,
	erro VARCHAR(80),
	enviado_em TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	UNIQUE (idempotency_key)
);

CREATE TABLE actions_map.acoes_map_login_limites (
	key VARCHAR(64) NOT NULL,
	attempts INTEGER NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (key)
);

CREATE TABLE actions_map.acoes_map_sessoes (
	token_hash VARCHAR(64) NOT NULL,
	profissional_id VARCHAR(160) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (token_hash)
);

CREATE TABLE actions_map.acoes_map_participacoes (
	id VARCHAR(36) NOT NULL,
	acao_id VARCHAR(36) NOT NULL,
	beneficiario_id VARCHAR(36) NOT NULL,
	local_indice INTEGER,
	origem VARCHAR(64),
	PRIMARY KEY (id),
	UNIQUE (origem),
	UNIQUE (acao_id, beneficiario_id),
	FOREIGN KEY(beneficiario_id) REFERENCES actions_map.acoes_map_beneficiarios (id),
	FOREIGN KEY(acao_id) REFERENCES actions_map.acoes_map_acoes (id)
);

CREATE INDEX ix_actions_map_acoes_map_participacoes_beneficiario_id ON actions_map.acoes_map_participacoes (beneficiario_id);

CREATE INDEX ix_actions_map_acoes_map_participacoes_acao_id ON actions_map.acoes_map_participacoes (acao_id);
