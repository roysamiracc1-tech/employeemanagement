--
-- PostgreSQL database dump
--

\restrict m6c4MySsm4OeC913SCQBJ7xJ5Q1fIkko3PrqwvSWxhKxjgy62klQ7uqcZqFe5pB

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
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.companies (id, name, industry, website, logo_url, hq_address, founded_year, description, is_active, created_at, updated_at, theme_color, header_html, footer_html) VALUES ('709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c', 'Acme Corp', 'Technology', NULL, '/static/uploads/logos/814d2b4fb1854049a17b79578201a154.png', 'HQ · Configure in Admin', NULL, NULL, true, '2026-04-25 16:26:58.932349', '2026-04-25 22:13:19.282414', '#0891b2', NULL, NULL);
INSERT INTO public.companies (id, name, industry, website, logo_url, hq_address, founded_year, description, is_active, created_at, updated_at, theme_color, header_html, footer_html) VALUES ('05a3fddb-0add-4a76-87c7-6bf0d84d214d', 'Telia', 'Telecommunications', NULL, '/static/uploads/logos/62884e09a102472d810a70ed09f11bb1.png', 'Tallinn, Estonia', 2010, NULL, true, '2026-04-26 10:02:33.305069', '2026-04-26 10:02:33.305069', '#7c3aed', NULL, NULL);
INSERT INTO public.companies (id, name, industry, website, logo_url, hq_address, founded_year, description, is_active, created_at, updated_at, theme_color, header_html, footer_html) VALUES ('6f50b11c-c330-40c6-8bda-4c08c2dca039', 'Sam Cpmapny', 'Technology', NULL, '/static/uploads/logos/911b76702a1e46ddaef58632fa297ab4.webp', 'Banglore, India', 2025, NULL, true, '2026-05-14 22:59:10.489491', '2026-05-14 22:59:10.489491', '#16a34a', NULL, NULL);


--
-- Data for Name: portal_features; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('41ff7908-f914-43fd-9643-7cd004b223f9', 'employee_profiles', 'Employee Profiles', 'View and manage employee personal, role and org data', 1);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('cc53bdea-fad5-4119-9a82-8145f94dc436', 'org_structure', 'Organisation Structure', 'Manage business units, locations and functional units', 2);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('40da374e-6ad3-45cb-aa82-8de661ae05a2', 'user_accounts', 'User Accounts', 'Create, enable/disable and assign roles to portal users', 3);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('ad909142-12fc-453c-95b5-b0f388983df4', 'skills', 'Skills & Certifications', 'View, validate and manage skill profiles', 4);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', 'vacations', 'Vacations & Leave', 'Manage vacation types, entitlements and leave requests', 5);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('dbfd34d9-57ae-42fd-8ddd-de6499d802ee', 'reports', 'Reports & Analytics', 'Access competency dashboards and analytics', 6);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('074152aa-7422-4cfb-8f12-caf46c425b2f', 'company_settings', 'Company Settings', 'Edit company branding, logo, theme and metadata', 7);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('9f6182e7-4c92-4e0d-ae98-2f3a7b6e12e9', 'system_config', 'System Configuration', 'Widget settings and global platform config', 8);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('89148e24-5192-4c13-bbe5-5a3dd4d81c3f', 'skills_intelligence', 'Skills Intelligence', 'Benchmark skill gaps and strengths against SO 2025 survey data', 9);
INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES ('e15c2322-f23c-48a0-b94a-5c517c8e9f86', 'org_change', 'Position Change Requests', 'Raise and approve employee business unit / department / manager changes', 10);


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.roles (id, name, description, company_id) VALUES ('73a197d8-da22-4b82-bb60-faaaa18aaac8', 'EMPLOYEE', 'View and manage own profile only', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('cf53e828-2a2c-4a50-bf53-47dd045e222c', 'SOLID_LINE_MANAGER', 'View and manage solid-line direct reports', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('8dfad483-141b-42ff-a904-455118738782', 'DOTTED_LINE_MANAGER', 'View dotted-line reports', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('fac43777-5b5d-410f-be93-1f431b170ca6', 'HIRING_MANAGER', 'Search employees within assigned hiring scope', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('d878ecd9-3ca6-4d1f-8ce0-856a0d4628c4', 'DEPARTMENT_HEAD', 'View all employees under their department/BU', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('c710059a-4088-4f44-be84-7689daf95ab5', 'LOCATION_HEAD', 'View all employees in their location', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', 'HR_ADMIN', 'Full employee record access based on HR permissions', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', 'SYSTEM_ADMIN', 'Full system-wide access and configuration', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', 'PORTAL_ADMIN', 'Full administrative access within their assigned company', NULL);
INSERT INTO public.roles (id, name, description, company_id) VALUES ('e196c16c-0128-41e3-9086-46c3bcc4fa3e', 'EMPLOYEE', 'View and manage own profile only', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('eb623694-748e-435f-961e-bca1cb7f6cba', 'EMPLOYEE', 'View and manage own profile only', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('a850fd1f-6f32-4cef-a4e7-620db54d2275', 'SOLID_LINE_MANAGER', 'View and manage solid-line direct reports', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('751a03cf-e6b6-42bf-bb10-039b2c268254', 'SOLID_LINE_MANAGER', 'View and manage solid-line direct reports', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('e2549181-ffe3-4611-a8dc-7aaf7ef56ab8', 'DOTTED_LINE_MANAGER', 'View dotted-line reports', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('fc36d8a2-1fd4-416b-ba75-2cb2d039085e', 'DOTTED_LINE_MANAGER', 'View dotted-line reports', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('97acbaf0-0c5d-4506-b577-c079d9aa9640', 'HIRING_MANAGER', 'Search employees within assigned hiring scope', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('540725f0-53fc-4964-8f7f-9debab02293c', 'HIRING_MANAGER', 'Search employees within assigned hiring scope', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('f933b261-549e-4f4b-8f0e-1aebb5d52d9f', 'DEPARTMENT_HEAD', 'View all employees under their department/BU', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('e88330a4-2fe9-4570-bcf2-8c709f958566', 'DEPARTMENT_HEAD', 'View all employees under their department/BU', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('ef36633e-ec2c-41a6-96f9-17bc0d07a386', 'LOCATION_HEAD', 'View all employees in their location', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('db96a45c-6461-4705-a857-0380d108b4e2', 'LOCATION_HEAD', 'View all employees in their location', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', 'HR_ADMIN', 'Full employee record access based on HR permissions', '709a1ece-a1f0-4aa2-9cfb-bf64f1fd9b9c');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', 'HR_ADMIN', 'Full employee record access based on HR permissions', '05a3fddb-0add-4a76-87c7-6bf0d84d214d');
INSERT INTO public.roles (id, name, description, company_id) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', 'COMPANY_ADMIN', 'Company Administrator — full access to manage the company portal', '6f50b11c-c330-40c6-8bda-4c08c2dca039');


--
-- Data for Name: role_feature_access; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('73a197d8-da22-4b82-bb60-faaaa18aaac8', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('cf53e828-2a2c-4a50-bf53-47dd045e222c', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('cf53e828-2a2c-4a50-bf53-47dd045e222c', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('cf53e828-2a2c-4a50-bf53-47dd045e222c', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('8dfad483-141b-42ff-a904-455118738782', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('8dfad483-141b-42ff-a904-455118738782', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('fac43777-5b5d-410f-be93-1f431b170ca6', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('fac43777-5b5d-410f-be93-1f431b170ca6', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('d878ecd9-3ca6-4d1f-8ce0-856a0d4628c4', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('d878ecd9-3ca6-4d1f-8ce0-856a0d4628c4', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('d878ecd9-3ca6-4d1f-8ce0-856a0d4628c4', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('c710059a-4088-4f44-be84-7689daf95ab5', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('c710059a-4088-4f44-be84-7689daf95ab5', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', '07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', '40da374e-6ad3-45cb-aa82-8de661ae05a2', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', '07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', '074152aa-7422-4cfb-8f12-caf46c425b2f', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', '40da374e-6ad3-45cb-aa82-8de661ae05a2', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', '07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', '074152aa-7422-4cfb-8f12-caf46c425b2f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', '9f6182e7-4c92-4e0d-ae98-2f3a7b6e12e9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('d878ecd9-3ca6-4d1f-8ce0-856a0d4628c4', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', false, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', '40da374e-6ad3-45cb-aa82-8de661ae05a2', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', '07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('cf53e828-2a2c-4a50-bf53-47dd045e222c', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('eb623694-748e-435f-961e-bca1cb7f6cba', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e196c16c-0128-41e3-9086-46c3bcc4fa3e', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('751a03cf-e6b6-42bf-bb10-039b2c268254', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('a850fd1f-6f32-4cef-a4e7-620db54d2275', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('751a03cf-e6b6-42bf-bb10-039b2c268254', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('a850fd1f-6f32-4cef-a4e7-620db54d2275', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('751a03cf-e6b6-42bf-bb10-039b2c268254', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('a850fd1f-6f32-4cef-a4e7-620db54d2275', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('fc36d8a2-1fd4-416b-ba75-2cb2d039085e', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e2549181-ffe3-4611-a8dc-7aaf7ef56ab8', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('fc36d8a2-1fd4-416b-ba75-2cb2d039085e', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e2549181-ffe3-4611-a8dc-7aaf7ef56ab8', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('540725f0-53fc-4964-8f7f-9debab02293c', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('97acbaf0-0c5d-4506-b577-c079d9aa9640', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('540725f0-53fc-4964-8f7f-9debab02293c', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('97acbaf0-0c5d-4506-b577-c079d9aa9640', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e88330a4-2fe9-4570-bcf2-8c709f958566', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('f933b261-549e-4f4b-8f0e-1aebb5d52d9f', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e88330a4-2fe9-4570-bcf2-8c709f958566', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('f933b261-549e-4f4b-8f0e-1aebb5d52d9f', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e88330a4-2fe9-4570-bcf2-8c709f958566', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('f933b261-549e-4f4b-8f0e-1aebb5d52d9f', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('db96a45c-6461-4705-a857-0380d108b4e2', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('ef36633e-ec2c-41a6-96f9-17bc0d07a386', '41ff7908-f914-43fd-9643-7cd004b223f9', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('db96a45c-6461-4705-a857-0380d108b4e2', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('ef36633e-ec2c-41a6-96f9-17bc0d07a386', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', '41ff7908-f914-43fd-9643-7cd004b223f9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', 'cc53bdea-fad5-4119-9a82-8145f94dc436', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', 'ad909142-12fc-453c-95b5-b0f388983df4', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', '07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', '07d7fd6e-b786-4811-b91c-2d1a4e7a3e1f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e88330a4-2fe9-4570-bcf2-8c709f958566', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', false, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('f933b261-549e-4f4b-8f0e-1aebb5d52d9f', 'dbfd34d9-57ae-42fd-8ddd-de6499d802ee', false, false, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('751a03cf-e6b6-42bf-bb10-039b2c268254', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('a850fd1f-6f32-4cef-a4e7-620db54d2275', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', '074152aa-7422-4cfb-8f12-caf46c425b2f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', '9f6182e7-4c92-4e0d-ae98-2f3a7b6e12e9', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('e0d21252-181d-4910-9805-e4d3b81f3f96', '89148e24-5192-4c13-bbe5-5a3dd4d81c3f', true, true, true);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('cf53e828-2a2c-4a50-bf53-47dd045e222c', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('0eb4ee9b-c826-4062-9034-d44aafa92462', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('56e31beb-e388-4fd8-82ef-83806d92acda', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('a850fd1f-6f32-4cef-a4e7-620db54d2275', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('751a03cf-e6b6-42bf-bb10-039b2c268254', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('1f5652d5-8a73-4f0e-adcb-b0cf8986f2ca', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('7255e9b1-919c-4421-ad09-190b4bc0a8e3', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, false);
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete) VALUES ('15bbfd36-f8f3-4077-aff5-0640ea17a598', 'e15c2322-f23c-48a0-b94a-5c517c8e9f86', true, true, true);


--
-- PostgreSQL database dump complete
--

\unrestrict m6c4MySsm4OeC913SCQBJ7xJ5Q1fIkko3PrqwvSWxhKxjgy62klQ7uqcZqFe5pB


--
-- ─────────────────────────────────────────────────────────────────────────────
-- Appended by hand (NOT part of the pg_dump above).
--
-- The `audit_log` portal feature and its grants (EP38 / KAN-187, ADR-009).
--
-- WHY THIS IS HERE AND NOT ONLY IN THE MIGRATION: `database/migrations/08_audit_log.sql`
-- §3 registers this feature, but a fresh database is built from `schema.sql`
-- (structure only) plus this file — migrations are NOT replayed (see
-- TECHNICAL_DOCUMENTATION §10). The feature row is DATA, so a schema-only dump
-- cannot carry it, and CI's fresh database had the audit_log TABLE but no
-- audit_log FEATURE. Any migration that seeds a row must add it here too.
--
-- Kept as INSERT…SELECT keyed on role NAME rather than hardcoded role ids so it
-- stays correct for the per-company roles as well, and cannot drift from the
-- role list above. Idempotent — safe if the migration has already run.
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO public.portal_features (id, code, label, description, sort_order) VALUES
    ('3f7c1d92-8a41-4e3b-9c6d-5b2e7a0f4c18', 'audit_log', 'Audit Log',
     'View the immutable audit trail of changes within the company', 13)
ON CONFLICT (code) DO NOTHING;

-- Read-only for PORTAL_ADMIN and HR_ADMIN. The table is append-only and there is
-- no legitimate audit write or delete outside audit_service, so write/delete are
-- FALSE for every tenant role. EMPLOYEE must never read the trail.
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, f.id, TRUE, FALSE, FALSE
FROM public.roles ro, public.portal_features f
WHERE f.code = 'audit_log'
  AND ro.name IN ('PORTAL_ADMIN', 'HR_ADMIN')
ON CONFLICT (role_id, feature_id) DO NOTHING;

-- SYSTEM_ADMIN mirrors the blanket grant elsewhere; the bypass in
-- _load_feature_access() makes this belt-and-braces rather than load-bearing.
INSERT INTO public.role_feature_access (role_id, feature_id, can_read, can_write, can_delete)
SELECT ro.id, f.id, TRUE, TRUE, TRUE
FROM public.roles ro, public.portal_features f
WHERE f.code = 'audit_log' AND ro.name = 'SYSTEM_ADMIN'
ON CONFLICT (role_id, feature_id) DO NOTHING;
