DROP TABLE IF EXISTS headers;
DROP TABLE IF EXISTS lobbying_activity;
DROP TABLE IF EXISTS pre_2020_lobbying_activity;
DROP TABLE IF EXISTS campaign_contributions;
DROP TABLE IF EXISTS client_compensation;

CREATE TABLE IF NOT EXISTS headers (
  header_id SERIAL,
  source_name VARCHAR(255),
  date_range VARCHAR(50),
  source_type VARCHAR(8),
  authorizing_officer_or_lobbyist_name VARCHAR(255),
  agent_type_or_title VARCHAR(255),
  business_name VARCHAR(255),
  address VARCHAR(255),
  city_state_zip_code VARCHAR(255),
  country VARCHAR(255),
  phone VARCHAR(50),
  url VARCHAR(150),
  PRIMARY KEY(source_name, date_range)
);

CREATE TABLE IF NOT EXISTS pre_2020_lobbying_activity (
  header_id VARCHAR(10),
  date VARCHAR(50),
  activity_or_bill_no_and_title VARCHAR(255),
  lobbyist_name VARCHAR(255),
  client_represented VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS lobbying_activity (
  header_id VARCHAR(10),
  lobbyist_name varchar(255),
  client_name varchar(255),
  house_or_senate VARCHAR(255),
  bill_number_or_agency_name VARCHAR(255),
  bill_title_or_activity TEXT,
  agent_position VARCHAR(255),
  amount VARCHAR(255),
  direct_business_association VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS campaign_contributions (
  header_id VARCHAR(10),
  date VARCHAR(50),
  recipient_name VARCHAR(255),
  lobbyist_name VARCHAR(255),
  office_sought VARCHAR(255),
  amount VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS client_compensation (
  header_id VARCHAR(10),
  client_name VARCHAR(255),
  amount VARCHAR(255)
);
