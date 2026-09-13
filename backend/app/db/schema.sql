--
-- PostgreSQL database dump
--

\restrict Xc5dH60hoArhwRaPMUKzBW4kRtLE7WOCTm1Z14u5yZ0zQk2lYAQwSrlrF97f7Jk

-- Dumped from database version 17.11 (Homebrew)
-- Dumped by pg_dump version 17.11 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: anomalies; Type: TABLE; Schema: public; Owner: mudit
--

CREATE TABLE public.anomalies (
    anomaly_id bigint NOT NULL,
    telemetry_id bigint NOT NULL,
    station_id character varying(50) NOT NULL,
    anomaly_type character varying(50),
    is_anomaly boolean NOT NULL,
    anomaly_score double precision,
    confidence double precision,
    severity character varying(20),
    affected_sensors text,
    explanation text,
    recommended_action text,
    detected_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.anomalies OWNER TO mudit;

--
-- Name: anomalies_anomaly_id_seq; Type: SEQUENCE; Schema: public; Owner: mudit
--

CREATE SEQUENCE public.anomalies_anomaly_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anomalies_anomaly_id_seq OWNER TO mudit;

--
-- Name: anomalies_anomaly_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mudit
--

ALTER SEQUENCE public.anomalies_anomaly_id_seq OWNED BY public.anomalies.anomaly_id;


--
-- Name: stations; Type: TABLE; Schema: public; Owner: mudit
--

CREATE TABLE public.stations (
    station_id character varying(50) NOT NULL,
    station_name character varying(100),
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    elevation double precision,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.stations OWNER TO mudit;

--
-- Name: telemetry; Type: TABLE; Schema: public; Owner: mudit
--

CREATE TABLE public.telemetry (
    telemetry_id bigint NOT NULL,
    station_id character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    temperature double precision,
    humidity double precision,
    pressure double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.telemetry OWNER TO mudit;

--
-- Name: telemetry_telemetry_id_seq; Type: SEQUENCE; Schema: public; Owner: mudit
--

CREATE SEQUENCE public.telemetry_telemetry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.telemetry_telemetry_id_seq OWNER TO mudit;

--
-- Name: telemetry_telemetry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mudit
--

ALTER SEQUENCE public.telemetry_telemetry_id_seq OWNED BY public.telemetry.telemetry_id;


--
-- Name: anomalies anomaly_id; Type: DEFAULT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.anomalies ALTER COLUMN anomaly_id SET DEFAULT nextval('public.anomalies_anomaly_id_seq'::regclass);


--
-- Name: telemetry telemetry_id; Type: DEFAULT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.telemetry ALTER COLUMN telemetry_id SET DEFAULT nextval('public.telemetry_telemetry_id_seq'::regclass);


--
-- Name: anomalies anomalies_pkey; Type: CONSTRAINT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.anomalies
    ADD CONSTRAINT anomalies_pkey PRIMARY KEY (anomaly_id);


--
-- Name: stations stations_pkey; Type: CONSTRAINT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.stations
    ADD CONSTRAINT stations_pkey PRIMARY KEY (station_id);


--
-- Name: telemetry telemetry_pkey; Type: CONSTRAINT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY (telemetry_id);


--
-- Name: anomalies anomalies_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.anomalies
    ADD CONSTRAINT anomalies_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.stations(station_id);


--
-- Name: anomalies anomalies_telemetry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.anomalies
    ADD CONSTRAINT anomalies_telemetry_id_fkey FOREIGN KEY (telemetry_id) REFERENCES public.telemetry(telemetry_id);


--
-- Name: telemetry fk_telemetry_station; Type: FK CONSTRAINT; Schema: public; Owner: mudit
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT fk_telemetry_station FOREIGN KEY (station_id) REFERENCES public.stations(station_id);


--
-- PostgreSQL database dump complete
--

\unrestrict Xc5dH60hoArhwRaPMUKzBW4kRtLE7WOCTm1Z14u5yZ0zQk2lYAQwSrlrF97f7Jk

-- ML training and validation dataset
CREATE TABLE IF NOT EXISTS training_data (
    training_id BIGSERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    timestamp TIMESTAMPTZ NOT NULL,

    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    pressure DOUBLE PRECISION,

    dataset_type VARCHAR(30) NOT NULL
        CHECK (dataset_type IN ('clean', 'anomaly_injected')),

    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_type VARCHAR(100),
    anomaly_id VARCHAR(100),

    original_temperature DOUBLE PRECISION,
    original_humidity DOUBLE PRECISION,
    original_pressure DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- ML prediction outputs
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    telemetry_id BIGINT REFERENCES telemetry(telemetry_id),
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    expected_temperature DOUBLE PRECISION,
    expected_pressure DOUBLE PRECISION,
    expected_humidity DOUBLE PRECISION,
    temperature_error DOUBLE PRECISION,
    pressure_error DOUBLE PRECISION,
    humidity_error DOUBLE PRECISION,
    anomaly_score DOUBLE PRECISION,
    model_version VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Sensor health tracking
CREATE TABLE IF NOT EXISTS sensor_health (
    health_id BIGSERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    health_score DOUBLE PRECISION,
    anomaly_count INTEGER DEFAULT 0,
    prediction_error DOUBLE PRECISION,
    communication_reliability DOUBLE PRECISION,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Operator alerts
CREATE TABLE IF NOT EXISTS alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    anomaly_id BIGINT REFERENCES anomalies(anomaly_id),
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    severity VARCHAR(30),
    status VARCHAR(30) DEFAULT 'NEW',
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);
