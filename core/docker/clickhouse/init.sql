CREATE DATABASE IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.kafka_vacancies_queue (
    event String,
    data String 
) ENGINE = Kafka
SETTINGS kafka_broker_list = 'redpanda:9092',
        kafka_topic_list = 'vacancies_events',
        kafka_group_name = 'clickhouse_dwh_consumer',
        kafka_format = 'JSONEachRow';

CREATE TABLE IF NOT EXISTS analytics.vacancies_log (
    event_time DateTime DEFAULT now(),
    event_type String,
    vacancy_id UInt64,
    title String,
    salary_from Float64
) ENGINE = MergeTree()
ORDER BY (event_time, vacancy_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.vacancies_mv TO analytics.vacancies_log AS
SELECT
    now() AS event_time,
    event AS event_type,
    JSONExtractUInt(data, 'vacancy_id') AS vacancy_id,
    JSONExtractString(data, 'title') AS title,
    JSONExtractFloat(data, 'salary_from') AS salary_from
FROM analytics.kafka_vacancies_queue;