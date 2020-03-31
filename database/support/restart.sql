start transaction;

use ictf;

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
                          key(script_id, tick_id),
                          key(against_team_id),
                          key(script_id, error));

drop table if exists team_connectivity_log;
create table team_connectivity_log (id int not null auto_increment, primary key(id),
                                    team_id int not null,
                                    latency double null default null,
                                    packetloss double not null default 1.0,
                                    created_on timestamp not null default current_timestamp,
                                    key(team_id),
                                    key(created_on));

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

drop table if exists team_scripts_run_status;
create table team_scripts_run_status (id int not null auto_increment, primary key(id),
                                      team_id int not null,
                                      tick_id int not null,
                                      json_list_of_scripts_to_run text not null,
                                      created_on timestamp not null default current_timestamp,
                                      key(tick_id));

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

drop table if exists ticks;
create table ticks (id int not null auto_increment, primary key(id),
                    time_to_change timestamp null,
                    created_on timestamp not null default current_timestamp,
                    key(time_to_change),
                    key(created_on),
                    key(time_to_change, created_on));

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

-- This table is here to allow the teams to vote for services
-- It is specific to the 2015 iCTF and should be removed
drop table if exists vote_services;
create table vote_services (team_id int not null,
                            service_1 int not null,
                            service_2 int not null,
                            service_3 int not null,
                       primary key(team_id));


-- This is to keep track of support requests
drop table if exists tickets;
create table tickets (id int not null auto_increment, primary key(id),
                    team_id int not null,
                    ts varchar(256) null,
                    subject varchar(256) null,
                    msg mediumblob null,
                    response mediumblob null,
                    done boolean default 0);


commit;
