-- =============================================================================
-- UT-RIS — Radiology Information System
-- PostgreSQL Schema DDL
-- Capstone Sistem Informasi, Universitas Terbuka
--
-- Tabel  : users, patients, appointments, studies, reports
-- Versi  : 1.0.0
-- =============================================================================

-- Enable UUID extension (opsional, untuk future use)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ENUM TYPES
-- =============================================================================

CREATE TYPE userrole AS ENUM (
    'admin',
    'dokter',
    'radiolog',
    'resepsionis'
);

CREATE TYPE gender AS ENUM (
    'L',   -- Laki-laki
    'P'    -- Perempuan
);

CREATE TYPE modality AS ENUM (
    'CR',  -- Computed Radiography
    'DX',  -- Digital X-Ray
    'CT',  -- Computed Tomography
    'MR',  -- Magnetic Resonance Imaging
    'US',  -- Ultrasonography
    'MG',  -- Mammography
    'NM',  -- Nuclear Medicine
    'PT',  -- PET Scan
    'XA',  -- X-Ray Angiography
    'RF'   -- Radiofluoroscopy
);

CREATE TYPE studystatus AS ENUM (
    'scheduled',
    'in_progress',
    'completed',
    'reported',
    'cancelled'
);

CREATE TYPE reportstatus AS ENUM (
    'draft',
    'pending_review',
    'finalized',
    'amended'
);

CREATE TYPE reportpriority AS ENUM (
    'routine',
    'urgent',
    'stat'
);

CREATE TYPE appointmentstatus AS ENUM (
    'pending',
    'confirmed',
    'checked_in',
    'completed',
    'cancelled',
    'no_show'
);

CREATE TYPE appointmentpriority AS ENUM (
    'routine',
    'urgent',
    'emergency'
);

-- =============================================================================
-- TABLE: users
-- Pengguna sistem: admin, dokter, radiolog, resepsionis
-- =============================================================================

CREATE TABLE users (
    id                  SERIAL          PRIMARY KEY,
    username            VARCHAR(50)     NOT NULL UNIQUE,
    email               VARCHAR(255)    NOT NULL UNIQUE,
    full_name           VARCHAR(255)    NOT NULL,
    hashed_password     VARCHAR(255)    NOT NULL,
    role                userrole        NOT NULL DEFAULT 'resepsionis',
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_username  ON users (username);
CREATE INDEX ix_users_email     ON users (email);
CREATE INDEX ix_users_role      ON users (role);

COMMENT ON TABLE  users                 IS 'Akun pengguna sistem RIS';
COMMENT ON COLUMN users.role            IS 'Peran pengguna: admin, dokter, radiolog, resepsionis';
COMMENT ON COLUMN users.hashed_password IS 'Password di-hash menggunakan bcrypt';

-- =============================================================================
-- TABLE: patients
-- Data demografis pasien
-- =============================================================================

CREATE TABLE patients (
    id                      SERIAL          PRIMARY KEY,
    medical_record_number   VARCHAR(20)     NOT NULL UNIQUE,
    full_name               VARCHAR(255)    NOT NULL,
    nik                     VARCHAR(16)     UNIQUE,
    date_of_birth           DATE            NOT NULL,
    gender                  gender          NOT NULL,
    phone_number            VARCHAR(20),
    address                 TEXT,
    blood_type              VARCHAR(5),
    allergies               TEXT,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_patients_mrn        ON patients (medical_record_number);
CREATE INDEX ix_patients_full_name  ON patients (full_name);
CREATE INDEX ix_patients_nik        ON patients (nik) WHERE nik IS NOT NULL;

COMMENT ON TABLE  patients                          IS 'Data pasien terdaftar';
COMMENT ON COLUMN patients.medical_record_number    IS 'Nomor rekam medis unik, format: MRN000001';
COMMENT ON COLUMN patients.nik                      IS 'Nomor Induk Kependudukan (16 digit)';

-- =============================================================================
-- TABLE: appointments
-- Jadwal pemeriksaan radiologi
-- =============================================================================

CREATE TABLE appointments (
    id                          SERIAL              PRIMARY KEY,
    appointment_number          VARCHAR(20)         NOT NULL UNIQUE,
    patient_id                  INTEGER             NOT NULL REFERENCES patients(id)  ON DELETE RESTRICT,
    referring_doctor_id         INTEGER             REFERENCES users(id)              ON DELETE SET NULL,
    created_by_id               INTEGER             REFERENCES users(id)              ON DELETE SET NULL,
    requested_modality          VARCHAR(10)         NOT NULL,
    body_part                   VARCHAR(100)        NOT NULL,
    clinical_indication         TEXT,
    preparation_instructions    TEXT,
    scheduled_datetime          TIMESTAMPTZ         NOT NULL,
    estimated_duration_minutes  INTEGER             NOT NULL DEFAULT 30,
    status                      appointmentstatus   NOT NULL DEFAULT 'pending',
    priority                    appointmentpriority NOT NULL DEFAULT 'routine',
    notes                       TEXT,
    cancellation_reason         VARCHAR(500),
    checked_in_at               TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_appointments_patient_id         ON appointments (patient_id);
CREATE INDEX ix_appointments_scheduled_datetime ON appointments (scheduled_datetime);
CREATE INDEX ix_appointments_status             ON appointments (status);
CREATE INDEX ix_appointments_patient_status     ON appointments (patient_id, status);
CREATE INDEX ix_appointments_status_priority    ON appointments (status, priority);

COMMENT ON TABLE  appointments                          IS 'Jadwal pemeriksaan radiologi';
COMMENT ON COLUMN appointments.appointment_number       IS 'Nomor jadwal unik, format: APT-YYYYMMDD-XXXX';
COMMENT ON COLUMN appointments.requested_modality       IS 'Modalitas yang diminta (CR, CT, MR, dll)';
COMMENT ON COLUMN appointments.preparation_instructions IS 'Instruksi persiapan untuk pasien';

-- =============================================================================
-- TABLE: studies
-- Sesi pemeriksaan radiologi yang dilaksanakan
-- =============================================================================

CREATE TABLE studies (
    id                          SERIAL          PRIMARY KEY,
    study_instance_uid          VARCHAR(64)     NOT NULL UNIQUE,
    accession_number            VARCHAR(20)     NOT NULL UNIQUE,
    patient_id                  INTEGER         NOT NULL REFERENCES patients(id)     ON DELETE RESTRICT,
    appointment_id              INTEGER         REFERENCES appointments(id)          ON DELETE SET NULL,
    referring_doctor_id         INTEGER         REFERENCES users(id)                 ON DELETE SET NULL,
    performing_radiologist_id   INTEGER         REFERENCES users(id)                 ON DELETE SET NULL,
    modality                    modality        NOT NULL,
    body_part                   VARCHAR(100)    NOT NULL,
    clinical_indication         TEXT,
    procedure_description       VARCHAR(255),
    status                      studystatus     NOT NULL DEFAULT 'scheduled',
    scheduled_at                TIMESTAMPTZ,
    started_at                  TIMESTAMPTZ,
    completed_at                TIMESTAMPTZ,
    technician_notes            TEXT,
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_studies_patient_id              ON studies (patient_id);
CREATE INDEX ix_studies_accession_number        ON studies (accession_number);
CREATE INDEX ix_studies_study_instance_uid      ON studies (study_instance_uid);
CREATE INDEX ix_studies_modality                ON studies (modality);
CREATE INDEX ix_studies_status                  ON studies (status);
CREATE INDEX ix_studies_scheduled_at            ON studies (scheduled_at);
CREATE INDEX ix_studies_patient_status          ON studies (patient_id, status);
CREATE INDEX ix_studies_modality_status         ON studies (modality, status);

COMMENT ON TABLE  studies                       IS 'Sesi pemeriksaan radiologi';
COMMENT ON COLUMN studies.study_instance_uid    IS 'UID unik kompatibel DICOM';
COMMENT ON COLUMN studies.accession_number      IS 'Nomor akses pemeriksaan, format: STD-YYYYMMDD-XXXXXX';
COMMENT ON COLUMN studies.modality              IS 'Jenis alat: CR, DX, CT, MR, US, MG, NM, PT, XA, RF';

-- =============================================================================
-- TABLE: reports
-- Laporan radiologi hasil interpretasi study
-- =============================================================================

CREATE TABLE reports (
    id                  SERIAL          PRIMARY KEY,
    report_number       VARCHAR(20)     NOT NULL UNIQUE,
    study_id            INTEGER         NOT NULL UNIQUE REFERENCES studies(id) ON DELETE RESTRICT,
    radiologist_id      INTEGER         NOT NULL REFERENCES users(id)          ON DELETE RESTRICT,
    verified_by_id      INTEGER         REFERENCES users(id)                   ON DELETE SET NULL,
    technique           TEXT,
    findings            TEXT            NOT NULL,
    impression          TEXT            NOT NULL,
    recommendation      TEXT,
    internal_notes      TEXT,
    status              reportstatus    NOT NULL DEFAULT 'draft',
    priority            reportpriority  NOT NULL DEFAULT 'routine',
    drafted_at          TIMESTAMPTZ,
    finalized_at        TIMESTAMPTZ,
    verified_at         TIMESTAMPTZ,
    amended_at          TIMESTAMPTZ,
    amendment_reason    VARCHAR(500),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Satu study hanya boleh punya satu report
    CONSTRAINT uq_reports_study_id UNIQUE (study_id),
    -- Verifikasi hanya bisa dilakukan oleh orang berbeda dari penulis
    CONSTRAINT chk_reports_verifier CHECK (verified_by_id IS NULL OR verified_by_id != radiologist_id)
);

CREATE INDEX ix_reports_study_id            ON reports (study_id);
CREATE INDEX ix_reports_radiologist_id      ON reports (radiologist_id);
CREATE INDEX ix_reports_status              ON reports (status);
CREATE INDEX ix_reports_priority            ON reports (priority);
CREATE INDEX ix_reports_finalized_at        ON reports (finalized_at);
CREATE INDEX ix_reports_radiologist_status  ON reports (radiologist_id, status);
CREATE INDEX ix_reports_status_priority     ON reports (status, priority);

COMMENT ON TABLE  reports                   IS 'Laporan radiologi hasil interpretasi';
COMMENT ON COLUMN reports.report_number     IS 'Nomor laporan unik, format: RPT-YYYYMMDD-XXXXXX';
COMMENT ON COLUMN reports.findings          IS 'Temuan radiologi — deskripsi objektif';
COMMENT ON COLUMN reports.impression        IS 'Kesimpulan / diagnosis radiologi';
COMMENT ON COLUMN reports.recommendation    IS 'Rekomendasi tindak lanjut (opsional)';
COMMENT ON COLUMN reports.internal_notes    IS 'Catatan internal, tidak tampil ke pasien';

-- =============================================================================
-- TRIGGER: auto-update updated_at on row change
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_studies_updated_at
    BEFORE UPDATE ON studies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SEED DATA: default admin user (password: admin123)
-- Hash dihasilkan dengan bcrypt rounds=12
-- GANTI PASSWORD INI SEBELUM DEPLOY KE PRODUCTION!
-- =============================================================================

INSERT INTO users (username, email, full_name, hashed_password, role) VALUES
(
    'admin',
    'admin@ut-ris.ac.id',
    'Administrator Sistem',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i',
    'admin'
),
(
    'dokter1',
    'dokter1@ut-ris.ac.id',
    'Dr. Budi Santoso, Sp.Rad',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i',
    'dokter'
),
(
    'rad1',
    'rad1@ut-ris.ac.id',
    'Dr. Siti Rahayu, Sp.Rad',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i',
    'radiolog'
),
(
    'resep1',
    'resep1@ut-ris.ac.id',
    'Ahmad Fauzi',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i',
    'resepsionis'
);
