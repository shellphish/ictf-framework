start transaction;

drop database if exists ictf;
create database ictf;
use ictf;

drop table if exists game;
create table game (id int);

drop table if exists teams;
create table teams (id int not null auto_increment, primary key(id),
                    name varchar(256) not null, unique key(name),
                    logo mediumblob null,
                    url varchar(256) null,
                    country char(128) null,
                    email varchar(256) not null, unique key(email),
                    password varchar(256) not null,
                    validated boolean default 0,
                    academic_team boolean default 0,
                    created_on timestamp not null default current_timestamp,
                    flag_token varchar(128) not null, unique key(flag_token),
                    login_token varchar(128) not null, unique key(login_token),
                    key(validated),
                    key(password));

drop table if exists team_vm_key;
create table team_vm_key (id int not null auto_increment, primary key(id),
                    team_id int not null, unique key(team_id),
                    ctf_key varchar(2048),
                    root_key varchar(2048),
                    ip varchar(20),
                    port int
                    );


drop table if exists team_metadata_labels;
create table team_metadata_labels (id int not null auto_increment, primary key(id),
                    label varchar(128) not null,
                    description varchar(1024) not null,
                    is_public boolean default false,
                    key(description (512)));

drop table if exists team_metadata;
create table team_metadata (id int not null auto_increment, primary key(id),
                            team_id int not null,
                            team_metadata_label_id int not null,
                            content varchar(1024) not null,
                            key(team_id),
                            key(team_metadata_label_id),
                            unique key(team_id, team_metadata_label_id));

drop table if exists services;
create table services (id int not null auto_increment, primary key(id),
                       name varchar(256) not null, unique key(id),
                       port smallint,
                       description text not null,
                       authors varchar(2048) null,
                       flag_id_description text not null,
                       team_id int not null, -- FIXME: associate service with author team, not needed anymore
                       upload_id int not null,
                       created_on timestamp not null default current_timestamp,
                       current_state enum('enabled', 'disabled') not null
                           default 'enabled',
                       key(current_state),
                       key(port));
ALTER TABLE services AUTO_INCREMENT=10001;

drop table if exists service_state;
create table service_state (id int not null auto_increment, primary key(id),
                            service_id int not null,
                            state enum('enabled', 'disabled') not null
                                default 'disabled',
                            reason text not null,
                            created_on timestamp not null
                                default current_timestamp,
                            tick_id int not null,
                            key(service_id, state),
                            key(service_id),
                            key(state),
                            key(tick_id),
                            key(tick_id, state),
                            key(created_on),
                            key(created_on, state),
                            key(service_id, created_on),
                            key(service_id, created_on, state));

-- todo: rename to team_service_state_log
drop table if exists team_service_state;
create table team_service_state (id int not null auto_increment, primary key(id),
                                 team_id int not null,
                                 service_id int not null,
                                 state enum('up', 'notfunctional', 'down', 'untested')
                                    not null default 'untested',
                                 reason text not null,
                                 created_on timestamp not null default current_timestamp,
                                 tick_id int not null,
                                 key(tick_id),
                                 key(tick_id, service_id),
                                 key(team_id, service_id),
                                 key(team_id),
                                 key(state),
                                 key(service_id, created_on),
                                 key(team_id, service_id, created_on),
                                 key(team_id, service_id, state),
                                 key(team_id, service_id, created_on, state));

-- todo: rename to team_service_state;
drop table if exists curr_team_service_state;
create table curr_team_service_state (tick_id int not null,
                                      team_id int not null,
                                      service_id int not null,
                                      state enum('up', 'notfunctional', 'down', 'untested')
                                         not null default 'untested',
                                      primary key(tick_id, team_id, service_id),
                                      key(tick_id, team_id),
                                      key(team_id, service_id),
                                      key(tick_id, service_id),
                                      key(tick_id),
                                      key(team_id),
                                      key(service_id));

drop table if exists team_score;
create table team_score (tick_id int not null,
                         team_id int not null,
                         service_points double not null,
                         attack_points double not null,
                         sla double not null,
                         total_points double not null,
                         num_valid_ticks int not null,
                         primary key(tick_id, team_id),
                         key(team_id),
                         key(tick_id),
                         key(tick_id, team_id));

drop table if exists team_connectivity_log;
create table team_connectivity_log (id int not null auto_increment, primary key(id),
                                    team_id int not null,
                                    latency double null default null,
                                    packetloss double not null default 1.0,
                                    created_on timestamp not null default current_timestamp,
                                    key(team_id),
                                    key(created_on));

drop table if exists scripts;
create table scripts (id int not null auto_increment, primary key(id),
                      filename VARCHAR (256),
                      type enum('exploit', 'benign', 'getflag', 'setflag') not null,
                      team_id int null default null,
                      service_id int not null,
                      upload_id int not null,
                      created_on timestamp not null default current_timestamp,
                      current_state enum('enabled', 'disabled') not null
                          default 'enabled',
                      key(current_state),
                      key(created_on),
                      key(team_id),
                      key(type),
                      key(service_id),
                      key(upload_id),
                      key(service_id, current_state),
                      key(service_id, team_id),
                      key(service_id, team_id, current_state));

drop table if exists script_state;
create table script_state (id int not null auto_increment, primary key(id),
                           script_id int not null,
                           state enum('enabled', 'disabled') not null
                               default 'disabled',
                           reason text not null,
                           created_on timestamp not null
                               default current_timestamp,
                           tick_id int not null,
                           key(tick_id),
                           key(tick_id, script_id),
                           key(script_id, state),
                           key(script_id),
                           key(state),
                           key(created_on),
                           key(created_on, state),
                           key(created_on, script_id),
                           key(created_on, script_id, state));

drop table if exists script_runs;
create table script_runs (id int not null auto_increment, primary key(id),
                          script_id int not null,
                          against_team_id int not null,
                          output text null default null,
                          error int default null,
                          error_message text null default null,
                          created_on timestamp not null default current_timestamp,
                          tick_id int not null,
                          key(tick_id),
                          key(tick_id, error),
                          key(script_id),
                          key(script_id, tick_id, against_team_id),
                          key(script_id, tick_id),
                          key(against_team_id),
                          key(script_id, error));

drop table if exists team_scripts_run_status;
create table team_scripts_run_status (id int not null auto_increment, primary key(id),
                                      team_id int not null,
                                      tick_id int not null,
                                      json_list_of_scripts_to_run text not null,
                                      created_on timestamp not null default current_timestamp,
                                      key(tick_id));

drop table if exists flags;
create table flags (id int not null auto_increment, primary key(id),
                    team_id int not null,
                    service_id int not null,
                    flag varchar(128) not null,
                    flag_id varchar(128),
                    cookie varchar(1024),
                    created_on timestamp not null default current_timestamp,
                    tick_id int not null,
                    key(flag),
                    key(tick_id),
                    key(team_id),
                    key(service_id),
                    key(created_on),
                    key(team_id, service_id),
                    key(team_id, service_id, created_on));

drop table if exists flag_submissions;
create table flag_submissions (id int not null auto_increment, primary key(id),
                              team_id int not null,
                              flag varchar(128) not null,
                              flag_id int null,
                              created_on timestamp not null default current_timestamp,
                              tick_id int not null,
                              service_id int null,
                              result enum('correct',
                                          'incorrect',
                                          'ownflag',
                                          'placetoolow',
                                          'alreadysubmitted',
                                          'notactive'),
                              key(team_id, tick_id, result),
                              key(team_id, tick_id),
                              key(tick_id, result),
                              key(tick_id),
                              key(service_id),
                              key(team_id),
                              key(flag_id),
                              key(flag),
                              key(result),
                              unique key(team_id, flag),
                              key(created_on));

drop table if exists ticks;
create table ticks (id int not null auto_increment, primary key(id),
                    time_to_change timestamp null,
                    created_on timestamp not null default current_timestamp,
                    key(time_to_change),
                    key(created_on),
                    key(time_to_change, created_on));

drop table if exists uploads;
create table uploads (id int not null auto_increment, primary key(id),
                      team_id int not null,
                      name VARCHAR (256) not null,
                      payload longblob not null,
                      upload_type enum('service', 'exploit') not null,
                      is_bundle tinyint(1) not null,
                      service_id int null,
                      feedback text null,
                      state enum('untested', 'working', 'notworking') not null default 'untested',
                      created_on timestamp not null default current_timestamp,
                      key(team_id),
                      key(upload_type),
                      key(created_on),
                      key(created_on, upload_type),
                      key(team_id, created_on),
                      key(team_id, created_on, upload_type),
                      key(team_id, created_on, upload_type, state));

drop table if exists tick_scores;
create table tick_scores (tick_id int not null,
                             team_id int not null,
                             sla_points float not null,
                             attack_points float not null,
                             defense_points float not null,
                             total_points float not null,
                             primary key(tick_id, team_id),
                             key(team_id),
                             key(tick_id, team_id));

-- table for computing scoring
drop table if exists partial_scores;
create table partial_scores (tick_id int not null,
                             team_id int not null,
                             sla_points float not null,
                             cumulative_timeliness_points float not null,
                             cumulative_diversity_points float not null,
                             leetness_points float not null,
                             primary key(tick_id, team_id),
                             key(team_id),
                             key(tick_id, team_id));

drop table if exists vpn_info;
create table vpn_info (team_id int not null,
                       vpn_config text not null,
                       primary key(team_id));

-- This table is here to allow the teams to vote for services
-- It is specific to the 2015 iCTF and should be removed
drop table if exists vote_services;
create table vote_services (team_id int not null,
                            service_1 int not null,
                            service_2 int not null,
                            service_3 int not null,
                       primary key(team_id));

-- This table is here to allow the teams to submit dashboards
-- It is specific to the 2015 iCTF and should be removed
drop table if exists dashboard_uploads;
create table dashboard_uploads (id int not null auto_increment, primary key(id),
                                team_id int not null,
                                name varchar(256) not null, unique key(name),
                                valid boolean default 1,
                                archive longblob not null);

-- This violates our coding convention. This MUST NOT be in the database. Why
-- is this here?
drop table if exists ticks_configuration;
create table ticks_configuration (name varchar(128), primary key(name),
                                  value int not null);

insert into ticks_configuration (name, value) values
    ('NUMBER_OF_BENIGN_SCRIPTS', 2),
    ('NUMBER_OF_EXPLOIT_SCRIPTS', 0),
    ('TICK_TIME_IN_SECONDS', 200),
    ('NUMBER_OF_GETFLAGS', 1);

drop table if exists tickets;
create table tickets (id int not null auto_increment, primary key(id),
                    team_id int not null,
                    ts varchar(256) null,
                    subject varchar(256) null,
                    msg mediumblob null,
                    response mediumblob null,					
                    done boolean default 0);

commit;
