CREATE TABLE merchants
(
    merchant_id         VARCHAR(50) PRIMARY KEY,
    economical_activity VARCHAR(50),
    name                VARCHAR(50),
    status              VARCHAR(20),
    remarks             TEXT
);

INSERT INTO merchants (merchant_id, economical_activity, name, status, remarks)
VALUES ('1', 'RETAIL', 'Juls', 'ACTIVE', 'You can not go wrong with Juls!');


CREATE TABLE payments
(
    payment_id               VARCHAR(50) PRIMARY KEY,
    merchant_id              VARCHAR(50)    NOT NULL,
    total_amount             DECIMAL(10, 2) NOT NULL,
    tip                      DECIMAL(10, 2) NOT NULL,
    vat                      DECIMAL(10, 2) NOT NULL,
    currency                 VARCHAR(3)     NOT NULL,
    card_masked_pan          VARCHAR(50)    NOT NULL,
    status                   VARCHAR(20)    NOT NULL,
    payment_date             BIGINT         NOT NULL,
    receipt_response_code    VARCHAR(50),
    receipt_response_message VARCHAR(50),
    receipt_approval_code    VARCHAR(50),
    FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id)
);

CREATE TABLE transactions
(
    transaction_id             VARCHAR(50) PRIMARY KEY,
    client_id                  VARCHAR(50)    NOT NULL,
    client_reference_id        VARCHAR(50)    NOT NULL,
    merchant_id                VARCHAR(50)    NOT NULL,
    transaction_type           VARCHAR(50)    NOT NULL,
    currency                   VARCHAR(3)     NOT NULL,
    total_amount               DECIMAL(10, 2) NOT NULL,
    tip                        DECIMAL(10, 2) NOT NULL,
    vat                        DECIMAL(10, 2) NOT NULL,
    status                     VARCHAR(20)    NOT NULL,
    transaction_date           BIGINT         NOT NULL,
    card_data_cardholder_name  VARCHAR(20),
    card_data_franchise        VARCHAR(20),
    card_data_category         VARCHAR(20),
    card_data_country          VARCHAR(20),
    card_data_masked_pan       VARCHAR(20),
    card_data_expiration_month INT,
    card_data_expiration_year  INT,
    network                    VARCHAR(50),
    response_code              VARCHAR(50),
    response_message           VARCHAR(50),
    approval_code              VARCHAR(10),
    attempt                    INT
);
