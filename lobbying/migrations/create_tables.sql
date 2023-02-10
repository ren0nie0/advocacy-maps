DROP TABLE IF EXISTS headers;
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS campaign_contributions;
DROP TABLE IF EXISTS client_compensation;

CREATE TABLE IF NOT EXISTS headers (
  source_name VARCHAR(255),
  date_range VARCHAR(255),
  authorizing_officer_name VARCHAR(255),
  lobbyist_name VARCHAR(255),
  title VARCHAR(255),
  business_name VARCHAR(255),
  address VARCHAR(255),
  city_state_zip_code VARCHAR(255),
  country VARCHAR(255),
  agent_type VARCHAR(255),
  phone VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS activities (
  source_name VARCHAR(255),
  date_range VARCHAR(255),
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
  source_name VARCHAR(255),
  date_range VARCHAR(255),
  date VARCHAR(255),
  recipient_name VARCHAR(255),
  lobbyist_name VARCHAR(255),
  office_sought VARCHAR(255),
  amount VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS client_compensation (
  source_name VARCHAR(255),
  date_range VARCHAR(255),
  client_name VARCHAR(255),
  amount VARCHAR(255)
);
