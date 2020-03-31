
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
                          key(script_id),
                          key(script_id, tick_id, against_team_id),
                          key(script_id, tick_id),
                          key(against_team_id),
                          key(script_id, error));
