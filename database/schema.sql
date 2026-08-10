--
-- PostgreSQL database dump
--

\restrict XiY6RKY4mDMxOg9WG7uxJWOUuRmRfembAemzlsOCUmUTwm0MLc9MGiUUryDTvF0

-- Dumped from database version 16.13 (Homebrew)
-- Dumped by pg_dump version 16.13 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

-- KAN-190 (T-190-1): exclusion constraints need this, and the effective-dated
-- pay tables in W2 will use them. Here so a fresh database built from this file
-- alone can create one.
CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: audit_log_immutable(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.audit_log_immutable() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (attempted %)', TG_OP
        USING ERRCODE = 'restrict_violation';
END; $$;


--
-- Name: fn_update_employee_search(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_update_employee_search() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO employee_search_index (employee_id, search_text)
    VALUES (
        NEW.id,
        to_tsvector('english',
            COALESCE(NEW.first_name, '')  || ' ' ||
            COALESCE(NEW.last_name,  '')  || ' ' ||
            COALESCE(NEW.job_title,  '')  || ' ' ||
            COALESCE(NEW.email,      '')
        )
    )
    ON CONFLICT (employee_id) DO UPDATE
        SET search_text = EXCLUDED.search_text;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id bigint NOT NULL,
    company_id uuid NOT NULL,
    actor_user_id uuid,
    actor_employee_id uuid,
    actor_label character varying(255) NOT NULL,
    actor_roles jsonb DEFAULT '[]'::jsonb NOT NULL,
    actor_ip character varying(45),
    actor_session_id character varying(64),
    subject_employee_id uuid,
    subject_employee_number character varying(50),
    action character varying(60) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    before_state jsonb,
    after_state jsonb,
    reason text NOT NULL,
    correlation_id uuid NOT NULL,
    outcome character varying(10) DEFAULT 'SUCCESS'::character varying NOT NULL,
    error_code character varying(60),
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    retention_class character varying(20) DEFAULT 'STANDARD'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_audit_outcome CHECK (((outcome)::text = ANY ((ARRAY['SUCCESS'::character varying, 'FAILED'::character varying])::text[]))),
    CONSTRAINT chk_audit_reason_not_blank CHECK ((btrim(reason) <> ''::text)),
    CONSTRAINT chk_audit_retention_class CHECK (((retention_class)::text = ANY ((ARRAY['STANDARD'::character varying, 'EMPLOYMENT'::character varying, 'SECURITY'::character varying])::text[])))
);


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: business_units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_units (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(150) NOT NULL,
    code character varying(50),
    description text,
    company_id uuid
);


--
-- Name: certifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.certifications (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(200) NOT NULL,
    provider character varying(150),
    description text
);


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(200) NOT NULL,
    industry character varying(100),
    website character varying(255),
    logo_url text,
    hq_address text,
    founded_year integer,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    theme_color character varying(7) DEFAULT '#2563eb'::character varying,
    header_html text,
    footer_html text
);


--
-- Name: company_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company_features (
    company_id uuid NOT NULL,
    feature_id uuid NOT NULL,
    is_enabled boolean DEFAULT false NOT NULL,
    enabled_at timestamp with time zone,
    enabled_by uuid,
    enabled_for_hr boolean DEFAULT false NOT NULL
);


--
-- Name: company_role_feature_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company_role_feature_access (
    company_id uuid NOT NULL,
    role_id uuid NOT NULL,
    feature_id uuid NOT NULL,
    updated_by uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    can_read boolean DEFAULT false NOT NULL,
    can_write boolean DEFAULT false NOT NULL,
    can_delete boolean DEFAULT false NOT NULL
);


--
-- Name: cost_centers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cost_centers (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    business_unit_id uuid,
    code character varying(50) NOT NULL,
    name character varying(150) NOT NULL
);


--
-- Name: dashboard_metric_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dashboard_metric_snapshots (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    snapshot_date date DEFAULT CURRENT_DATE NOT NULL,
    dimension_type character varying(50) NOT NULL,
    dimension_id uuid,
    skill_id uuid,
    skill_category_id uuid,
    average_rating numeric(4,2),
    employee_count integer DEFAULT 0 NOT NULL,
    rating_count integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT dashboard_metric_snapshots_dimension_type_check CHECK (((dimension_type)::text = ANY ((ARRAY['COMPANY'::character varying, 'LOCATION'::character varying, 'BUSINESS_UNIT'::character varying, 'FUNCTIONAL_UNIT'::character varying, 'COST_CENTER'::character varying, 'SOLID_LINE_MANAGER'::character varying, 'DOTTED_LINE_MANAGER'::character varying, 'JOB_TITLE'::character varying])::text[])))
);


--
-- Name: dashboard_saved_filters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dashboard_saved_filters (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    filter_name character varying(150) NOT NULL,
    filter_json jsonb NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: employee_certifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_certifications (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_id uuid NOT NULL,
    certification_id uuid NOT NULL,
    issued_date date,
    expiry_date date,
    certificate_url text,
    verification_status character varying(50) DEFAULT 'UNVERIFIED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT employee_certifications_verification_status_check CHECK (((verification_status)::text = ANY ((ARRAY['UNVERIFIED'::character varying, 'VERIFIED'::character varying, 'EXPIRED'::character varying, 'REJECTED'::character varying])::text[])))
);


--
-- Name: employee_directory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_directory (
    employee_id integer NOT NULL,
    employee_name character varying(100) NOT NULL,
    initials character varying(5),
    email character varying(150),
    phone character varying(30),
    department character varying(50),
    product_unit_department character varying(60),
    location character varying(50),
    designation character varying(80),
    skills text,
    skill_ratings text,
    experience_years integer,
    hire_date date,
    solid_line_manager_id integer,
    solid_line_manager_name character varying(100),
    dotted_line_manager_id integer,
    dotted_line_manager_name character varying(100)
);


--
-- Name: employee_directory_employee_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_directory_employee_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_directory_employee_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_directory_employee_id_seq OWNED BY public.employee_directory.employee_id;


--
-- Name: employee_import_rows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_import_rows (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    import_id uuid NOT NULL,
    row_number integer NOT NULL,
    raw_data jsonb NOT NULL,
    validation_errors jsonb,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    employee_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: employee_imports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_imports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    uploaded_by uuid NOT NULL,
    status character varying(30) DEFAULT 'PENDING_REVIEW'::character varying NOT NULL,
    filename character varying(255),
    row_count integer DEFAULT 0 NOT NULL,
    valid_count integer DEFAULT 0 NOT NULL,
    error_count integer DEFAULT 0 NOT NULL,
    imported_count integer DEFAULT 0 NOT NULL,
    approved_by uuid,
    approved_at timestamp without time zone,
    processed_at timestamp without time zone,
    reject_reason text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: employee_org_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_org_assignments (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_id uuid NOT NULL,
    location_id uuid,
    business_unit_id uuid,
    functional_unit_id uuid,
    cost_center_id uuid,
    effective_from date DEFAULT CURRENT_DATE NOT NULL,
    effective_to date,
    is_current boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: employee_search_index; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_search_index (
    employee_id uuid NOT NULL,
    search_text tsvector,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: employee_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_skills (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_id uuid NOT NULL,
    skill_id uuid NOT NULL,
    self_rating_level_id uuid,
    manager_validated_level_id uuid,
    years_of_experience numeric(4,1),
    last_used_date date,
    is_primary_skill boolean DEFAULT false NOT NULL,
    validation_status character varying(50) DEFAULT 'SELF_ASSESSED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT employee_skills_validation_status_check CHECK (((validation_status)::text = ANY ((ARRAY['SELF_ASSESSED'::character varying, 'PENDING_MANAGER_VALIDATION'::character varying, 'VALIDATED'::character varying, 'REJECTED'::character varying])::text[])))
);


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_number character varying(50) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    phone_number character varying(50),
    job_title character varying(150),
    employment_status character varying(50) DEFAULT 'ACTIVE'::character varying NOT NULL,
    employment_type character varying(50),
    join_date date,
    exit_date date,
    profile_photo_url text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    company_id uuid,
    gender character varying(10),
    CONSTRAINT employees_employment_status_check CHECK (((employment_status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'INACTIVE'::character varying, 'RESIGNED'::character varying, 'TERMINATED'::character varying])::text[]))),
    CONSTRAINT employees_employment_type_check CHECK (((employment_type)::text = ANY ((ARRAY['PERMANENT'::character varying, 'CONTRACTOR'::character varying, 'INTERN'::character varying, 'PART_TIME'::character varying])::text[]))),
    CONSTRAINT employees_gender_check CHECK (((gender)::text = ANY ((ARRAY['MALE'::character varying, 'FEMALE'::character varying, 'OTHER'::character varying])::text[])))
);


--
-- Name: functional_units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.functional_units (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    business_unit_id uuid,
    name character varying(150) NOT NULL,
    code character varying(50),
    description text,
    company_id uuid
);


--
-- Name: locations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.locations (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(150) NOT NULL,
    country character varying(100),
    city character varying(100),
    office_code character varying(50),
    company_id uuid
);


--
-- Name: manager_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.manager_relationships (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_id uuid NOT NULL,
    manager_id uuid NOT NULL,
    relationship_type character varying(50) NOT NULL,
    effective_from date DEFAULT CURRENT_DATE NOT NULL,
    effective_to date,
    is_current boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_not_self_manager CHECK ((employee_id <> manager_id)),
    CONSTRAINT manager_relationships_relationship_type_check CHECK (((relationship_type)::text = ANY ((ARRAY['SOLID_LINE'::character varying, 'DOTTED_LINE'::character varying])::text[])))
);


--
-- Name: notification_mutes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_mutes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    company_id uuid NOT NULL,
    event_type character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: notification_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    event_type character varying(50) NOT NULL,
    recipient_role character varying(50) NOT NULL,
    is_enabled boolean DEFAULT true NOT NULL,
    allow_mute boolean DEFAULT true NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: org_change_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_change_approvals (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    request_id uuid NOT NULL,
    step_order integer NOT NULL,
    approver_type character varying(10) NOT NULL,
    approver_role character varying(50),
    approver_employee_id uuid,
    decided_by_user_id uuid,
    decision character varying(10),
    note text,
    decided_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT org_change_approvals_decision_check CHECK (((decision)::text = ANY ((ARRAY['APPROVED'::character varying, 'REJECTED'::character varying])::text[])))
);


--
-- Name: org_change_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_change_requests (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    employee_id uuid NOT NULL,
    requested_by_user_id uuid NOT NULL,
    reason text,
    from_business_unit_id uuid,
    from_functional_unit_id uuid,
    from_location_id uuid,
    from_manager_id uuid,
    proposed_business_unit_id uuid,
    proposed_functional_unit_id uuid,
    proposed_location_id uuid,
    proposed_manager_id uuid,
    workflow_id uuid,
    current_step integer DEFAULT 1 NOT NULL,
    effective_date date,
    status character varying(12) DEFAULT 'PENDING'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    decided_at timestamp without time zone,
    CONSTRAINT org_change_requests_status_check CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'CANCELLED'::character varying])::text[])))
);


--
-- Name: org_change_workflow_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_change_workflow_steps (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workflow_id uuid NOT NULL,
    step_order integer NOT NULL,
    approver_type character varying(10) NOT NULL,
    approver_role character varying(50),
    approver_employee_id uuid,
    label character varying(120),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT org_change_workflow_steps_approver_type_check CHECK (((approver_type)::text = ANY ((ARRAY['ROLE'::character varying, 'EMPLOYEE'::character varying])::text[]))),
    CONSTRAINT org_change_workflow_steps_check CHECK (((((approver_type)::text = 'ROLE'::text) AND (approver_role IS NOT NULL) AND (approver_employee_id IS NULL)) OR (((approver_type)::text = 'EMPLOYEE'::text) AND (approver_employee_id IS NOT NULL) AND (approver_role IS NULL))))
);


--
-- Name: org_change_workflows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_change_workflows (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    name character varying(150) DEFAULT 'Position Change Approval'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: page_views; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.page_views (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    employee_id uuid,
    company_id uuid,
    role character varying(60),
    route character varying(200) NOT NULL,
    page_label character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    permission_code character varying(100) NOT NULL,
    description text
);


--
-- Name: portal_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portal_features (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    code character varying(100) NOT NULL,
    label character varying(150) NOT NULL,
    description text,
    sort_order integer DEFAULT 0 NOT NULL,
    default_enabled boolean DEFAULT true NOT NULL
);


--
-- Name: proficiency_levels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.proficiency_levels (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    level_name character varying(100) NOT NULL,
    level_order integer NOT NULL,
    description text
);


--
-- Name: role_feature_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_feature_access (
    role_id uuid NOT NULL,
    feature_id uuid NOT NULL,
    can_read boolean DEFAULT false NOT NULL,
    can_write boolean DEFAULT false NOT NULL,
    can_delete boolean DEFAULT false NOT NULL
);


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    company_id uuid
);


--
-- Name: saved_views; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saved_views (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    view_name character varying(150) NOT NULL,
    view_type character varying(100),
    filter_json jsonb,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: search_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.search_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    company_id uuid,
    role character varying(60),
    query text NOT NULL,
    result_count integer,
    search_type character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: skill_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_categories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(150) NOT NULL,
    description text
);


--
-- Name: skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skills (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    skill_category_id uuid,
    name character varying(150) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL
);


--
-- Name: survey_benchmarks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_benchmarks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    survey_source character varying(100) NOT NULL,
    survey_year smallint NOT NULL,
    category character varying(100) NOT NULL,
    technology character varying(200) NOT NULL,
    usage_pct numeric(5,1) NOT NULL,
    context character varying(50) DEFAULT 'all_respondents'::character varying NOT NULL,
    rank_in_category smallint,
    source_url text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    desired_pct numeric(5,1),
    admired_pct numeric(5,1),
    sankey_role character varying(30)
);


--
-- Name: user_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    event_type character varying(60) NOT NULL,
    message text NOT NULL,
    link text,
    is_read boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    related_type character varying(40),
    related_id uuid
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    assigned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_id uuid,
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text,
    is_active boolean DEFAULT true NOT NULL,
    last_login_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    theme_preference character varying(10) DEFAULT 'light'::character varying,
    CONSTRAINT users_theme_preference_check CHECK (((theme_preference)::text = ANY ((ARRAY['light'::character varying, 'dark'::character varying])::text[])))
);


--
-- Name: vacation_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vacation_requests (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    employee_id uuid NOT NULL,
    vacation_type_id uuid NOT NULL,
    manager_id uuid,
    start_date date NOT NULL,
    end_date date NOT NULL,
    working_days integer DEFAULT 1 NOT NULL,
    notes text,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    manager_note text,
    reviewed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_vr_dates CHECK ((end_date >= start_date)),
    CONSTRAINT chk_vr_days CHECK ((working_days > 0)),
    CONSTRAINT chk_vr_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'CANCELLED'::character varying])::text[])))
);


--
-- Name: vacation_type_locations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vacation_type_locations (
    vacation_type_id uuid NOT NULL,
    location_id uuid NOT NULL
);


--
-- Name: vacation_type_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vacation_type_rules (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    vacation_type_id uuid NOT NULL,
    rule_type character varying(50) NOT NULL,
    rule_value character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_rule_type CHECK (((rule_type)::text = ANY ((ARRAY['GENDER_EQ'::character varying, 'MIN_TENURE_MONTHS'::character varying, 'MIN_TENURE_YEARS'::character varying])::text[])))
);


--
-- Name: vacation_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vacation_types (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    max_days_per_year integer,
    is_paid boolean DEFAULT true NOT NULL,
    color character varying(7) DEFAULT '#3b82f6'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: visibility_scopes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visibility_scopes (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    scope_type character varying(50) NOT NULL,
    scope_value_id uuid,
    effective_from date DEFAULT CURRENT_DATE NOT NULL,
    effective_to date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT visibility_scopes_scope_type_check CHECK (((scope_type)::text = ANY ((ARRAY['COMPANY'::character varying, 'LOCATION'::character varying, 'BUSINESS_UNIT'::character varying, 'FUNCTIONAL_UNIT'::character varying, 'COST_CENTER'::character varying])::text[])))
);


--
-- Name: widget_refresh_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.widget_refresh_settings (
    role_name character varying(50) NOT NULL,
    interval_ms integer DEFAULT 30000 NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: employee_directory employee_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_directory ALTER COLUMN employee_id SET DEFAULT nextval('public.employee_directory_employee_id_seq'::regclass);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: business_units business_units_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_units
    ADD CONSTRAINT business_units_code_key UNIQUE (code);


--
-- Name: business_units business_units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_units
    ADD CONSTRAINT business_units_pkey PRIMARY KEY (id);


--
-- Name: certifications certifications_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certifications
    ADD CONSTRAINT certifications_name_key UNIQUE (name);


--
-- Name: certifications certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certifications
    ADD CONSTRAINT certifications_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: company_features company_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_features
    ADD CONSTRAINT company_features_pkey PRIMARY KEY (company_id, feature_id);


--
-- Name: company_role_feature_access company_role_feature_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_role_feature_access
    ADD CONSTRAINT company_role_feature_access_pkey PRIMARY KEY (company_id, role_id, feature_id);


--
-- Name: cost_centers cost_centers_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cost_centers
    ADD CONSTRAINT cost_centers_code_key UNIQUE (code);


--
-- Name: cost_centers cost_centers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cost_centers
    ADD CONSTRAINT cost_centers_pkey PRIMARY KEY (id);


--
-- Name: dashboard_metric_snapshots dashboard_metric_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_metric_snapshots
    ADD CONSTRAINT dashboard_metric_snapshots_pkey PRIMARY KEY (id);


--
-- Name: dashboard_saved_filters dashboard_saved_filters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_saved_filters
    ADD CONSTRAINT dashboard_saved_filters_pkey PRIMARY KEY (id);


--
-- Name: employee_certifications employee_certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications
    ADD CONSTRAINT employee_certifications_pkey PRIMARY KEY (id);


--
-- Name: employee_directory employee_directory_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_directory
    ADD CONSTRAINT employee_directory_email_key UNIQUE (email);


--
-- Name: employee_directory employee_directory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_directory
    ADD CONSTRAINT employee_directory_pkey PRIMARY KEY (employee_id);


--
-- Name: employee_import_rows employee_import_rows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_import_rows
    ADD CONSTRAINT employee_import_rows_pkey PRIMARY KEY (id);


--
-- Name: employee_imports employee_imports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_imports
    ADD CONSTRAINT employee_imports_pkey PRIMARY KEY (id);


--
-- Name: employee_org_assignments employee_org_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_org_assignments
    ADD CONSTRAINT employee_org_assignments_pkey PRIMARY KEY (id);


--
-- Name: employee_search_index employee_search_index_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_search_index
    ADD CONSTRAINT employee_search_index_employee_id_key UNIQUE (employee_id);


--
-- Name: employee_search_index employee_search_index_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_search_index
    ADD CONSTRAINT employee_search_index_pkey PRIMARY KEY (employee_id);


--
-- Name: employee_skills employee_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_pkey PRIMARY KEY (id);


--
-- Name: employees employees_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_email_key UNIQUE (email);


--
-- Name: employees employees_employee_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_employee_number_key UNIQUE (employee_number);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: functional_units functional_units_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.functional_units
    ADD CONSTRAINT functional_units_code_key UNIQUE (code);


--
-- Name: functional_units functional_units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.functional_units
    ADD CONSTRAINT functional_units_pkey PRIMARY KEY (id);


--
-- Name: locations locations_office_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_office_code_key UNIQUE (office_code);


--
-- Name: locations locations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_pkey PRIMARY KEY (id);


--
-- Name: manager_relationships manager_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manager_relationships
    ADD CONSTRAINT manager_relationships_pkey PRIMARY KEY (id);


--
-- Name: notification_mutes notification_mutes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_mutes
    ADD CONSTRAINT notification_mutes_pkey PRIMARY KEY (id);


--
-- Name: notification_mutes notification_mutes_user_id_event_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_mutes
    ADD CONSTRAINT notification_mutes_user_id_event_type_key UNIQUE (user_id, event_type);


--
-- Name: notification_settings notification_settings_company_id_event_type_recipient_role_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_settings
    ADD CONSTRAINT notification_settings_company_id_event_type_recipient_role_key UNIQUE (company_id, event_type, recipient_role);


--
-- Name: notification_settings notification_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_settings
    ADD CONSTRAINT notification_settings_pkey PRIMARY KEY (id);


--
-- Name: org_change_approvals org_change_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_approvals
    ADD CONSTRAINT org_change_approvals_pkey PRIMARY KEY (id);


--
-- Name: org_change_approvals org_change_approvals_request_id_step_order_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_approvals
    ADD CONSTRAINT org_change_approvals_request_id_step_order_key UNIQUE (request_id, step_order);


--
-- Name: org_change_requests org_change_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_pkey PRIMARY KEY (id);


--
-- Name: org_change_workflow_steps org_change_workflow_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflow_steps
    ADD CONSTRAINT org_change_workflow_steps_pkey PRIMARY KEY (id);


--
-- Name: org_change_workflow_steps org_change_workflow_steps_workflow_id_step_order_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflow_steps
    ADD CONSTRAINT org_change_workflow_steps_workflow_id_step_order_key UNIQUE (workflow_id, step_order);


--
-- Name: org_change_workflows org_change_workflows_company_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflows
    ADD CONSTRAINT org_change_workflows_company_id_key UNIQUE (company_id);


--
-- Name: org_change_workflows org_change_workflows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflows
    ADD CONSTRAINT org_change_workflows_pkey PRIMARY KEY (id);


--
-- Name: page_views page_views_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_views
    ADD CONSTRAINT page_views_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_permission_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_permission_code_key UNIQUE (permission_code);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: portal_features portal_features_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_features
    ADD CONSTRAINT portal_features_code_key UNIQUE (code);


--
-- Name: portal_features portal_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_features
    ADD CONSTRAINT portal_features_pkey PRIMARY KEY (id);


--
-- Name: proficiency_levels proficiency_levels_level_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proficiency_levels
    ADD CONSTRAINT proficiency_levels_level_name_key UNIQUE (level_name);


--
-- Name: proficiency_levels proficiency_levels_level_order_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proficiency_levels
    ADD CONSTRAINT proficiency_levels_level_order_key UNIQUE (level_order);


--
-- Name: proficiency_levels proficiency_levels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proficiency_levels
    ADD CONSTRAINT proficiency_levels_pkey PRIMARY KEY (id);


--
-- Name: role_feature_access role_feature_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_feature_access
    ADD CONSTRAINT role_feature_access_pkey PRIMARY KEY (role_id, feature_id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: saved_views saved_views_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_views
    ADD CONSTRAINT saved_views_pkey PRIMARY KEY (id);


--
-- Name: search_logs search_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.search_logs
    ADD CONSTRAINT search_logs_pkey PRIMARY KEY (id);


--
-- Name: skill_categories skill_categories_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_categories
    ADD CONSTRAINT skill_categories_name_key UNIQUE (name);


--
-- Name: skill_categories skill_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_categories
    ADD CONSTRAINT skill_categories_pkey PRIMARY KEY (id);


--
-- Name: skills skills_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_name_key UNIQUE (name);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (id);


--
-- Name: survey_benchmarks survey_benchmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_benchmarks
    ADD CONSTRAINT survey_benchmarks_pkey PRIMARY KEY (id);


--
-- Name: survey_benchmarks survey_benchmarks_survey_source_survey_year_category_techno_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_benchmarks
    ADD CONSTRAINT survey_benchmarks_survey_source_survey_year_category_techno_key UNIQUE (survey_source, survey_year, category, technology, context);


--
-- Name: employee_skills uq_employee_skill; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT uq_employee_skill UNIQUE (employee_id, skill_id);


--
-- Name: user_notifications user_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_notifications
    ADD CONSTRAINT user_notifications_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vacation_requests vacation_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_pkey PRIMARY KEY (id);


--
-- Name: vacation_type_locations vacation_type_locations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_type_locations
    ADD CONSTRAINT vacation_type_locations_pkey PRIMARY KEY (vacation_type_id, location_id);


--
-- Name: vacation_type_rules vacation_type_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_type_rules
    ADD CONSTRAINT vacation_type_rules_pkey PRIMARY KEY (id);


--
-- Name: vacation_types vacation_types_company_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_types
    ADD CONSTRAINT vacation_types_company_id_name_key UNIQUE (company_id, name);


--
-- Name: vacation_types vacation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_types
    ADD CONSTRAINT vacation_types_pkey PRIMARY KEY (id);


--
-- Name: visibility_scopes visibility_scopes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visibility_scopes
    ADD CONSTRAINT visibility_scopes_pkey PRIMARY KEY (id);


--
-- Name: widget_refresh_settings widget_refresh_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.widget_refresh_settings
    ADD CONSTRAINT widget_refresh_settings_pkey PRIMARY KEY (role_name);


--
-- Name: idx_audit_company_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_company_time ON public.audit_log USING btree (company_id, created_at DESC);


--
-- Name: idx_audit_correlation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_correlation ON public.audit_log USING btree (company_id, correlation_id);


--
-- Name: idx_audit_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_entity ON public.audit_log USING btree (company_id, entity_type, entity_id, created_at DESC);


--
-- Name: idx_business_units_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_units_company ON public.business_units USING btree (company_id);


--
-- Name: idx_co_feat_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_co_feat_lookup ON public.company_features USING btree (company_id, feature_id);


--
-- Name: idx_crfa_company_feature; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crfa_company_feature ON public.company_role_feature_access USING btree (company_id, feature_id);


--
-- Name: idx_dashboard_snap_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dashboard_snap_date ON public.dashboard_metric_snapshots USING btree (snapshot_date);


--
-- Name: idx_dashboard_snap_dim; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dashboard_snap_dim ON public.dashboard_metric_snapshots USING btree (dimension_type, dimension_id);


--
-- Name: idx_dashboard_snap_skill; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dashboard_snap_skill ON public.dashboard_metric_snapshots USING btree (skill_id);


--
-- Name: idx_emp_certs_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_certs_employee ON public.employee_certifications USING btree (employee_id);


--
-- Name: idx_emp_skills_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_skills_employee ON public.employee_skills USING btree (employee_id);


--
-- Name: idx_emp_skills_skill; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_skills_skill ON public.employee_skills USING btree (skill_id);


--
-- Name: idx_emp_skills_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_skills_status ON public.employee_skills USING btree (validation_status);


--
-- Name: idx_employees_company_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_company_status ON public.employees USING btree (company_id, employment_status);


--
-- Name: idx_employees_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_email ON public.employees USING btree (email);


--
-- Name: idx_employees_job_title; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_job_title ON public.employees USING btree (job_title);


--
-- Name: idx_functional_units_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_functional_units_company ON public.functional_units USING btree (company_id);


--
-- Name: idx_import_rows_import; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_import_rows_import ON public.employee_import_rows USING btree (import_id);


--
-- Name: idx_import_rows_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_import_rows_status ON public.employee_import_rows USING btree (status);


--
-- Name: idx_imports_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_imports_company ON public.employee_imports USING btree (company_id);


--
-- Name: idx_imports_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_imports_status ON public.employee_imports USING btree (status);


--
-- Name: idx_locations_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_locations_company ON public.locations USING btree (company_id);


--
-- Name: idx_mgr_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mgr_current ON public.manager_relationships USING btree (is_current);


--
-- Name: idx_mgr_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mgr_employee ON public.manager_relationships USING btree (employee_id);


--
-- Name: idx_mgr_manager; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mgr_manager ON public.manager_relationships USING btree (manager_id);


--
-- Name: idx_mgr_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mgr_type ON public.manager_relationships USING btree (relationship_type);


--
-- Name: idx_oca_request; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oca_request ON public.org_change_approvals USING btree (request_id);


--
-- Name: idx_ocr_company_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ocr_company_status ON public.org_change_requests USING btree (company_id, status);


--
-- Name: idx_ocr_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ocr_employee ON public.org_change_requests USING btree (employee_id);


--
-- Name: idx_ocr_requester; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ocr_requester ON public.org_change_requests USING btree (requested_by_user_id);


--
-- Name: idx_org_bu; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_bu ON public.employee_org_assignments USING btree (business_unit_id);


--
-- Name: idx_org_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_current ON public.employee_org_assignments USING btree (is_current);


--
-- Name: idx_org_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_employee ON public.employee_org_assignments USING btree (employee_id);


--
-- Name: idx_org_fu; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_fu ON public.employee_org_assignments USING btree (functional_unit_id);


--
-- Name: idx_org_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_location ON public.employee_org_assignments USING btree (location_id);


--
-- Name: idx_pv_company_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pv_company_created ON public.page_views USING btree (company_id, created_at DESC);


--
-- Name: idx_pv_route_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pv_route_created ON public.page_views USING btree (route, created_at DESC);


--
-- Name: idx_pv_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pv_user_created ON public.page_views USING btree (user_id, created_at DESC);


--
-- Name: idx_sb_category_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sb_category_year ON public.survey_benchmarks USING btree (survey_year, category);


--
-- Name: idx_search_text; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_search_text ON public.employee_search_index USING gin (search_text);


--
-- Name: idx_sl_company_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sl_company_created ON public.search_logs USING btree (company_id, created_at DESC);


--
-- Name: idx_sl_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sl_query ON public.search_logs USING btree (company_id, query, created_at DESC);


--
-- Name: idx_user_notif_user_unread; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_notif_user_unread ON public.user_notifications USING btree (user_id, is_read, created_at DESC);


--
-- Name: idx_user_notifications_related_unread; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_notifications_related_unread ON public.user_notifications USING btree (related_type, related_id) WHERE (NOT is_read);


--
-- Name: idx_vacation_requests_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vacation_requests_type ON public.vacation_requests USING btree (vacation_type_id);


--
-- Name: idx_visibility_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_visibility_scope ON public.visibility_scopes USING btree (scope_type, scope_value_id);


--
-- Name: idx_visibility_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_visibility_user ON public.visibility_scopes USING btree (user_id);


--
-- Name: idx_vr_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vr_employee ON public.vacation_requests USING btree (employee_id);


--
-- Name: idx_vr_manager; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vr_manager ON public.vacation_requests USING btree (manager_id);


--
-- Name: idx_vr_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vr_status ON public.vacation_requests USING btree (status);


--
-- Name: idx_vtr_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vtr_type ON public.vacation_type_rules USING btree (vacation_type_id);


--
-- Name: roles_company_name_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX roles_company_name_uniq ON public.roles USING btree (name, company_id) WHERE (company_id IS NOT NULL);


--
-- Name: roles_global_name_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX roles_global_name_uniq ON public.roles USING btree (name) WHERE (company_id IS NULL);


--
-- Name: audit_log trg_audit_log_no_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON public.audit_log FOR EACH ROW EXECUTE FUNCTION public.audit_log_immutable();


--
-- Name: employees trg_employee_search; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_employee_search AFTER INSERT OR UPDATE OF first_name, last_name, job_title, email ON public.employees FOR EACH ROW EXECUTE FUNCTION public.fn_update_employee_search();


--
-- Name: audit_log audit_log_actor_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_actor_employee_id_fkey FOREIGN KEY (actor_employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: audit_log audit_log_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: audit_log audit_log_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: audit_log audit_log_subject_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_subject_employee_id_fkey FOREIGN KEY (subject_employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: business_units business_units_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_units
    ADD CONSTRAINT business_units_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: company_features company_features_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_features
    ADD CONSTRAINT company_features_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: company_features company_features_enabled_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_features
    ADD CONSTRAINT company_features_enabled_by_fkey FOREIGN KEY (enabled_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: company_features company_features_feature_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_features
    ADD CONSTRAINT company_features_feature_id_fkey FOREIGN KEY (feature_id) REFERENCES public.portal_features(id) ON DELETE CASCADE;


--
-- Name: company_role_feature_access company_role_feature_access_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_role_feature_access
    ADD CONSTRAINT company_role_feature_access_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: company_role_feature_access company_role_feature_access_feature_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_role_feature_access
    ADD CONSTRAINT company_role_feature_access_feature_id_fkey FOREIGN KEY (feature_id) REFERENCES public.portal_features(id) ON DELETE CASCADE;


--
-- Name: company_role_feature_access company_role_feature_access_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_role_feature_access
    ADD CONSTRAINT company_role_feature_access_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: company_role_feature_access company_role_feature_access_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_role_feature_access
    ADD CONSTRAINT company_role_feature_access_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: cost_centers cost_centers_business_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cost_centers
    ADD CONSTRAINT cost_centers_business_unit_id_fkey FOREIGN KEY (business_unit_id) REFERENCES public.business_units(id) ON DELETE SET NULL;


--
-- Name: dashboard_metric_snapshots dashboard_metric_snapshots_skill_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_metric_snapshots
    ADD CONSTRAINT dashboard_metric_snapshots_skill_category_id_fkey FOREIGN KEY (skill_category_id) REFERENCES public.skill_categories(id) ON DELETE SET NULL;


--
-- Name: dashboard_metric_snapshots dashboard_metric_snapshots_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_metric_snapshots
    ADD CONSTRAINT dashboard_metric_snapshots_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE SET NULL;


--
-- Name: dashboard_saved_filters dashboard_saved_filters_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_saved_filters
    ADD CONSTRAINT dashboard_saved_filters_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: employee_certifications employee_certifications_certification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications
    ADD CONSTRAINT employee_certifications_certification_id_fkey FOREIGN KEY (certification_id) REFERENCES public.certifications(id);


--
-- Name: employee_certifications employee_certifications_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications
    ADD CONSTRAINT employee_certifications_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_import_rows employee_import_rows_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_import_rows
    ADD CONSTRAINT employee_import_rows_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: employee_import_rows employee_import_rows_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_import_rows
    ADD CONSTRAINT employee_import_rows_import_id_fkey FOREIGN KEY (import_id) REFERENCES public.employee_imports(id) ON DELETE CASCADE;


--
-- Name: employee_imports employee_imports_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_imports
    ADD CONSTRAINT employee_imports_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: employee_imports employee_imports_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_imports
    ADD CONSTRAINT employee_imports_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: employee_imports employee_imports_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_imports
    ADD CONSTRAINT employee_imports_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: employee_org_assignments employee_org_assignments_business_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_org_assignments
    ADD CONSTRAINT employee_org_assignments_business_unit_id_fkey FOREIGN KEY (business_unit_id) REFERENCES public.business_units(id);


--
-- Name: employee_org_assignments employee_org_assignments_cost_center_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_org_assignments
    ADD CONSTRAINT employee_org_assignments_cost_center_id_fkey FOREIGN KEY (cost_center_id) REFERENCES public.cost_centers(id);


--
-- Name: employee_org_assignments employee_org_assignments_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_org_assignments
    ADD CONSTRAINT employee_org_assignments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_org_assignments employee_org_assignments_functional_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_org_assignments
    ADD CONSTRAINT employee_org_assignments_functional_unit_id_fkey FOREIGN KEY (functional_unit_id) REFERENCES public.functional_units(id);


--
-- Name: employee_org_assignments employee_org_assignments_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_org_assignments
    ADD CONSTRAINT employee_org_assignments_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id);


--
-- Name: employee_search_index employee_search_index_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_search_index
    ADD CONSTRAINT employee_search_index_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_skills employee_skills_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_skills employee_skills_manager_validated_level_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_manager_validated_level_id_fkey FOREIGN KEY (manager_validated_level_id) REFERENCES public.proficiency_levels(id);


--
-- Name: employee_skills employee_skills_self_rating_level_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_self_rating_level_id_fkey FOREIGN KEY (self_rating_level_id) REFERENCES public.proficiency_levels(id);


--
-- Name: employee_skills employee_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: employees employees_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: functional_units functional_units_business_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.functional_units
    ADD CONSTRAINT functional_units_business_unit_id_fkey FOREIGN KEY (business_unit_id) REFERENCES public.business_units(id) ON DELETE SET NULL;


--
-- Name: functional_units functional_units_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.functional_units
    ADD CONSTRAINT functional_units_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: locations locations_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: manager_relationships manager_relationships_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manager_relationships
    ADD CONSTRAINT manager_relationships_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: manager_relationships manager_relationships_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manager_relationships
    ADD CONSTRAINT manager_relationships_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: notification_mutes notification_mutes_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_mutes
    ADD CONSTRAINT notification_mutes_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: notification_mutes notification_mutes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_mutes
    ADD CONSTRAINT notification_mutes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notification_settings notification_settings_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_settings
    ADD CONSTRAINT notification_settings_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: org_change_approvals org_change_approvals_approver_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_approvals
    ADD CONSTRAINT org_change_approvals_approver_employee_id_fkey FOREIGN KEY (approver_employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: org_change_approvals org_change_approvals_decided_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_approvals
    ADD CONSTRAINT org_change_approvals_decided_by_user_id_fkey FOREIGN KEY (decided_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: org_change_approvals org_change_approvals_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_approvals
    ADD CONSTRAINT org_change_approvals_request_id_fkey FOREIGN KEY (request_id) REFERENCES public.org_change_requests(id) ON DELETE CASCADE;


--
-- Name: org_change_requests org_change_requests_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: org_change_requests org_change_requests_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: org_change_requests org_change_requests_from_business_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_from_business_unit_id_fkey FOREIGN KEY (from_business_unit_id) REFERENCES public.business_units(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_from_functional_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_from_functional_unit_id_fkey FOREIGN KEY (from_functional_unit_id) REFERENCES public.functional_units(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_from_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_from_location_id_fkey FOREIGN KEY (from_location_id) REFERENCES public.locations(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_from_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_from_manager_id_fkey FOREIGN KEY (from_manager_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_proposed_business_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_proposed_business_unit_id_fkey FOREIGN KEY (proposed_business_unit_id) REFERENCES public.business_units(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_proposed_functional_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_proposed_functional_unit_id_fkey FOREIGN KEY (proposed_functional_unit_id) REFERENCES public.functional_units(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_proposed_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_proposed_location_id_fkey FOREIGN KEY (proposed_location_id) REFERENCES public.locations(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_proposed_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_proposed_manager_id_fkey FOREIGN KEY (proposed_manager_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: org_change_requests org_change_requests_requested_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_requested_by_user_id_fkey FOREIGN KEY (requested_by_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: org_change_requests org_change_requests_workflow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_requests
    ADD CONSTRAINT org_change_requests_workflow_id_fkey FOREIGN KEY (workflow_id) REFERENCES public.org_change_workflows(id) ON DELETE SET NULL;


--
-- Name: org_change_workflow_steps org_change_workflow_steps_approver_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflow_steps
    ADD CONSTRAINT org_change_workflow_steps_approver_employee_id_fkey FOREIGN KEY (approver_employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: org_change_workflow_steps org_change_workflow_steps_workflow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflow_steps
    ADD CONSTRAINT org_change_workflow_steps_workflow_id_fkey FOREIGN KEY (workflow_id) REFERENCES public.org_change_workflows(id) ON DELETE CASCADE;


--
-- Name: org_change_workflows org_change_workflows_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_change_workflows
    ADD CONSTRAINT org_change_workflows_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: page_views page_views_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_views
    ADD CONSTRAINT page_views_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE SET NULL;


--
-- Name: page_views page_views_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_views
    ADD CONSTRAINT page_views_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: page_views page_views_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_views
    ADD CONSTRAINT page_views_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: role_feature_access role_feature_access_feature_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_feature_access
    ADD CONSTRAINT role_feature_access_feature_id_fkey FOREIGN KEY (feature_id) REFERENCES public.portal_features(id) ON DELETE CASCADE;


--
-- Name: role_feature_access role_feature_access_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_feature_access
    ADD CONSTRAINT role_feature_access_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: roles roles_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: saved_views saved_views_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_views
    ADD CONSTRAINT saved_views_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: search_logs search_logs_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.search_logs
    ADD CONSTRAINT search_logs_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE SET NULL;


--
-- Name: search_logs search_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.search_logs
    ADD CONSTRAINT search_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: skills skills_skill_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_skill_category_id_fkey FOREIGN KEY (skill_category_id) REFERENCES public.skill_categories(id) ON DELETE SET NULL;


--
-- Name: user_notifications user_notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_notifications
    ADD CONSTRAINT user_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: vacation_requests vacation_requests_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: vacation_requests vacation_requests_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.employees(id);


--
-- Name: vacation_requests vacation_requests_vacation_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_requests
    ADD CONSTRAINT vacation_requests_vacation_type_id_fkey FOREIGN KEY (vacation_type_id) REFERENCES public.vacation_types(id);


--
-- Name: vacation_type_locations vacation_type_locations_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_type_locations
    ADD CONSTRAINT vacation_type_locations_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id) ON DELETE CASCADE;


--
-- Name: vacation_type_locations vacation_type_locations_vacation_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_type_locations
    ADD CONSTRAINT vacation_type_locations_vacation_type_id_fkey FOREIGN KEY (vacation_type_id) REFERENCES public.vacation_types(id) ON DELETE CASCADE;


--
-- Name: vacation_type_rules vacation_type_rules_vacation_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_type_rules
    ADD CONSTRAINT vacation_type_rules_vacation_type_id_fkey FOREIGN KEY (vacation_type_id) REFERENCES public.vacation_types(id) ON DELETE CASCADE;


--
-- Name: vacation_types vacation_types_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacation_types
    ADD CONSTRAINT vacation_types_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: visibility_scopes visibility_scopes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visibility_scopes
    ADD CONSTRAINT visibility_scopes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict XiY6RKY4mDMxOg9WG7uxJWOUuRmRfembAemzlsOCUmUTwm0MLc9MGiUUryDTvF0



--
-- ─────────────────────────────────────────────────────────────────────────────
-- JOB ARCHITECTURE (KAN-190 · EP42 W1) — migration 12_job_architecture.sql
--
-- Hand-added rather than swept in by a full `pg_dump` regeneration, so the diff
-- shows exactly the new objects and nothing that had drifted onto a dev database
-- by hand. Keep it in step with the migration; `TestJobArchitectureSchemaParity`
-- fails the build if they diverge.
-- ─────────────────────────────────────────────────────────────────────────────
--

CREATE TABLE public.job_families (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(150) NOT NULL,
    description text,
    sort_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.job_levels (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    job_family_id uuid NOT NULL,
    ordinal integer NOT NULL,
    title character varying(150) NOT NULL,
    short_code character varying(20),
    step_count integer NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_job_levels_ordinal CHECK (((ordinal >= 1) AND (ordinal <= 30))),
    CONSTRAINT chk_job_levels_step_count CHECK (((step_count >= 1) AND (step_count <= 12)))
);

COMMENT ON COLUMN public.job_levels.step_count IS 'Number of increments ABOVE entry (EP42 §12.4.1). step_count = 5 means SIX steps: .0 .1 .2 .3 .4 .5. Never defaulted — the configurator must require an answer.';

CREATE TABLE public.job_step_expectations (
    job_level_id uuid NOT NULL,
    company_id uuid NOT NULL,
    step_no integer NOT NULL,
    summary character varying(200) NOT NULL,
    description text NOT NULL,
    drafted_by character varying(150),
    updated_by_user_id uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_jse_step CHECK (((step_no >= 0) AND (step_no <= 12))),
    CONSTRAINT chk_jse_text CHECK (((btrim((summary)::text) <> ''::text) AND (btrim(description) <> ''::text)))
);

CREATE TABLE public.employee_job_assignments (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    employee_id uuid NOT NULL,
    job_level_id uuid NOT NULL,
    step_no integer,
    effective_from date DEFAULT CURRENT_DATE NOT NULL,
    effective_to date,
    is_current boolean DEFAULT true NOT NULL,
    assigned_by_user_id uuid,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_eja_dates CHECK (((effective_to IS NULL) OR (effective_to > effective_from))),
    CONSTRAINT chk_eja_step CHECK (((step_no IS NULL) OR ((step_no >= 0) AND (step_no <= 12))))
);

COMMENT ON COLUMN public.employee_job_assignments.step_no IS 'NULL = STEP_NOT_ASSESSED, a distinct state and NOT step 0 (EP42 A6). No derived base pay, not evaluable, renders "Step not yet assessed".';

ALTER TABLE ONLY public.job_families ADD CONSTRAINT job_families_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.job_families ADD CONSTRAINT job_families_company_id_code_key UNIQUE (company_id, code);
ALTER TABLE ONLY public.job_families ADD CONSTRAINT job_families_company_id_name_key UNIQUE (company_id, name);
ALTER TABLE ONLY public.job_families ADD CONSTRAINT job_families_id_company_id_key UNIQUE (id, company_id);

ALTER TABLE ONLY public.job_levels ADD CONSTRAINT job_levels_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.job_levels ADD CONSTRAINT job_levels_job_family_id_ordinal_key UNIQUE (job_family_id, ordinal);
ALTER TABLE ONLY public.job_levels ADD CONSTRAINT job_levels_job_family_id_title_key UNIQUE (job_family_id, title);
ALTER TABLE ONLY public.job_levels ADD CONSTRAINT job_levels_id_company_id_key UNIQUE (id, company_id);

ALTER TABLE ONLY public.job_step_expectations ADD CONSTRAINT job_step_expectations_pkey PRIMARY KEY (job_level_id, step_no);
ALTER TABLE ONLY public.employee_job_assignments ADD CONSTRAINT employee_job_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.job_families
    ADD CONSTRAINT job_families_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.job_levels
    ADD CONSTRAINT fk_job_levels_family FOREIGN KEY (job_family_id, company_id) REFERENCES public.job_families(id, company_id) ON DELETE RESTRICT;
ALTER TABLE ONLY public.job_step_expectations
    ADD CONSTRAINT fk_jse_level FOREIGN KEY (job_level_id, company_id) REFERENCES public.job_levels(id, company_id) ON DELETE CASCADE;
ALTER TABLE ONLY public.job_step_expectations
    ADD CONSTRAINT job_step_expectations_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.employee_job_assignments
    ADD CONSTRAINT employee_job_assignments_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.employee_job_assignments
    ADD CONSTRAINT employee_job_assignments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.employee_job_assignments
    ADD CONSTRAINT fk_eja_level FOREIGN KEY (job_level_id, company_id) REFERENCES public.job_levels(id, company_id) ON DELETE RESTRICT;
ALTER TABLE ONLY public.employee_job_assignments
    ADD CONSTRAINT employee_job_assignments_assigned_by_user_id_fkey FOREIGN KEY (assigned_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

CREATE INDEX idx_job_families_company ON public.job_families USING btree (company_id, is_active, sort_order);
CREATE INDEX idx_job_levels_family ON public.job_levels USING btree (company_id, job_family_id, ordinal);
CREATE INDEX idx_jse_company ON public.job_step_expectations USING btree (company_id, job_level_id, step_no);
CREATE INDEX idx_eja_employee ON public.employee_job_assignments USING btree (employee_id, is_current);
CREATE INDEX idx_eja_level ON public.employee_job_assignments USING btree (company_id, job_level_id);

--
-- The step bound as a CONSTRAINT, not a convention (EP42 §12.4.1). `step_no`
-- lives on employee_job_assignments and `step_count` on job_levels, so no
-- single-table CHECK can express it. A step_no of 6 on a step_count = 5 level
-- produces a pay point compounded six times — a wrong salary, not a cosmetic
-- error — so TD-21 is closed rather than accepted.
--

CREATE OR REPLACE FUNCTION public.employee_job_assignment_step_valid() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE max_step INT;
BEGIN
    IF NEW.step_no IS NULL THEN
        RETURN NEW;
    END IF;
    SELECT step_count INTO max_step FROM job_levels WHERE id = NEW.job_level_id;
    IF max_step IS NULL THEN
        RAISE EXCEPTION 'job level % does not exist', NEW.job_level_id;
    END IF;
    IF NEW.step_no < 0 OR NEW.step_no > max_step THEN
        RAISE EXCEPTION 'step_no % is outside level %''s ladder: valid steps are 0..% (step_count counts increments ABOVE entry, so a step_count of % yields % discrete values). EP42 ADR-017 §12.4.1.',
                        NEW.step_no, NEW.job_level_id, max_step, max_step, max_step + 1;
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_eja_step_valid
    BEFORE INSERT OR UPDATE OF step_no, job_level_id ON public.employee_job_assignments
    FOR EACH ROW EXECUTE FUNCTION public.employee_job_assignment_step_valid();


--
-- ─────────────────────────────────────────────────────────────────────────────
-- STEP ROADMAPS + THE STEP-DISCLOSURE SWITCH (KAN-207 · EP42 W1)
--   migration 14_step_roadmaps.sql
--
-- ⚠ NO RATINGS, NO SCORES, NO ASSESSMENT COLUMNS, EVER. A roadmap is a statement
-- of expectations; a scored judgement about a person is a different legal object
-- (GDPR Art. 22 / EU AI Act) with different obligations. Guarded by
-- TestNoAssessmentColumnsOnTheLadder.
-- ─────────────────────────────────────────────────────────────────────────────
--

ALTER TABLE public.companies
    ADD COLUMN IF NOT EXISTS display_step_to_employee boolean DEFAULT true NOT NULL;

COMMENT ON COLUMN public.companies.display_step_to_employee IS 'Whether an employee is shown their own STEP NUMBER (EP42 KAN-190/207, A2 §6). Governs display only, never inference: the employee still reads the whole ladder and their own expectations either way. Default TRUE.';

CREATE TABLE public.employee_step_roadmaps (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    company_id uuid NOT NULL,
    employee_id uuid NOT NULL,
    version integer NOT NULL,
    from_job_level_id uuid NOT NULL,
    from_step_no integer NOT NULL,
    target_job_level_id uuid NOT NULL,
    target_step_no integer NOT NULL,
    content text NOT NULL,
    review_context character varying(24) NOT NULL,
    review_date date,
    authored_by_user_id uuid NOT NULL,
    authored_by_label character varying(255) NOT NULL,
    authored_at timestamp with time zone DEFAULT now() NOT NULL,
    acknowledged_at timestamp with time zone,
    acknowledged_by_user_id uuid,
    superseded_at timestamp with time zone,
    correlation_id uuid NOT NULL,
    CONSTRAINT chk_esr_ack CHECK (((acknowledged_at IS NULL) = (acknowledged_by_user_id IS NULL))),
    CONSTRAINT chk_esr_content CHECK ((btrim(content) <> ''::text)),
    CONSTRAINT chk_esr_context CHECK (((review_context)::text = ANY ((ARRAY['PROBATION_REVIEW'::character varying, 'MID_TERM_GOAL_REVIEW'::character varying, 'PERFORMANCE_REVIEW'::character varying, 'OFF_CYCLE'::character varying])::text[]))),
    CONSTRAINT chk_esr_steps CHECK (((from_step_no >= 0) AND (target_step_no >= 0))),
    CONSTRAINT chk_esr_version CHECK ((version >= 1))
);

ALTER TABLE ONLY public.employee_step_roadmaps ADD CONSTRAINT employee_step_roadmaps_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.employee_step_roadmaps ADD CONSTRAINT employee_step_roadmaps_employee_id_version_key UNIQUE (employee_id, version);

ALTER TABLE ONLY public.employee_step_roadmaps
    ADD CONSTRAINT employee_step_roadmaps_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.employee_step_roadmaps
    ADD CONSTRAINT employee_step_roadmaps_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.employee_step_roadmaps
    ADD CONSTRAINT employee_step_roadmaps_authored_by_user_id_fkey FOREIGN KEY (authored_by_user_id) REFERENCES public.users(id);
ALTER TABLE ONLY public.employee_step_roadmaps
    ADD CONSTRAINT employee_step_roadmaps_acknowledged_by_user_id_fkey FOREIGN KEY (acknowledged_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.employee_step_roadmaps
    ADD CONSTRAINT fk_esr_target FOREIGN KEY (target_job_level_id, company_id) REFERENCES public.job_levels(id, company_id) ON DELETE RESTRICT;
ALTER TABLE ONLY public.employee_step_roadmaps
    ADD CONSTRAINT fk_esr_from FOREIGN KEY (from_job_level_id, company_id) REFERENCES public.job_levels(id, company_id) ON DELETE RESTRICT;

-- Exactly one LIVE roadmap per employee. A new version supersedes the previous one
-- inside the same transaction; the previous one stays READABLE, which is the whole
-- reason this is versioned rather than updated in place.
CREATE UNIQUE INDEX uq_esr_one_live ON public.employee_step_roadmaps USING btree (employee_id) WHERE (superseded_at IS NULL);
CREATE INDEX idx_esr_unacknowledged ON public.employee_step_roadmaps USING btree (company_id, authored_by_user_id) WHERE ((acknowledged_at IS NULL) AND (superseded_at IS NULL));
CREATE INDEX idx_esr_employee ON public.employee_step_roadmaps USING btree (employee_id, version DESC);
