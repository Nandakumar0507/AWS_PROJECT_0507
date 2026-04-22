CREATE DATABASE IF NOT EXISTS graphene_trace CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE graphene_trace;

-- Django manages schema via migrations. This file documents the normalized structure:
-- Users -> auth_app_customuser
-- Patients -> auth_app_patientprofile
-- Clinicians -> auth_app_clinicianprofile
-- SensorData -> data_app_sensordata
-- Alerts -> data_app_alert
-- Metrics -> data_app_metric
-- Comments -> data_app_comment
-- Replies -> data_app_reply

-- Example index strategy for large time-series workloads:
-- CREATE INDEX idx_sensor_user_time ON data_app_sensordata (user_id, timestamp);
-- CREATE INDEX idx_metric_user_time ON data_app_metric (user_id, timestamp);
