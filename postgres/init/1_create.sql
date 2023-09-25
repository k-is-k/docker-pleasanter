/* DATABASEを作成 */
create user "Implem.Pleasanter_Owner" with password 'SetAdminsPWD';
create user "Implem.Pleasanter_User" with password 'SetUsersPWD';
create schema authorization "Implem.Pleasanter_Owner";

/* DATABASEを作成 */
create database "Implem.Pleasanter" with owner "Implem.Pleasanter_Owner";
\c "Implem.Pleasanter";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
