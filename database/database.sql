start transaction;

drop table if exists teams;
drop table if exists scripts;
drop table if exists services;
drop table if exists team_service_state;
drop table if exists exploit_attacks;
drop table if exists flags;
drop table if exists flag_submission;	 
drop table if exists script_runs;
drop table if exists script_payload;
drop table if exists ticks;
drop table if exists game;
drop table if exists team_scripts_run_status;
drop table if exists team_score;

create table game (id int);

create table teams (id int not null auto_increment, primary key(id),
	   		 	   	team_name varchar(256) not null, unique key(id),
					ip_range varchar(24) not null,
					created_on varchar(30) not null);
					
create table services (id int not null auto_increment, primary key(id),
	   		 		   name varchar(256) not null, unique key(id),
					   port int not null,
					   description text not null,
					   authors varchar(2048) not null,
					   flag_id_description varchar(2048) not null,					   
					   created_on varchar(30) not null);

create table team_service_state (id int not null auto_increment, primary key(id),
	   		 					 team_id int(11) not null,
								 service_id int (11) not null,
								 state tinyint(2) not null,
								 reason varchar(256) not null,
								 created_on varchar(30) not null,
								 key(team_id, service_id),
								 key(team_id),
								 key(state),
								 key(team_id, service_id, created_on),
								 key(state, team_id, service_id, created_on));


create table team_score (id int not null auto_increment, primary key(id),
	   		 			 team_id int(11) not null,
						 score int not null,
						 reason varchar(256) not null,
						 created_on varchar(30) not null,
						 key(team_id),
						 key(created_on));

create table scripts (id int not null auto_increment, primary key(id),
	   		 		   name varchar(64),
	   		 		   is_ours tinyint(1) not null,
					   type varchar(24) not null,
	   		 		   team_id int(11),
					   service_id int(11) not null,
					   is_working tinyint(1),
					   is_bundle tinyint(1) not null,
					   latest_script tinyint(1) not null,
					   feedback text,
					   created_on varchar(30) not null,
					   key(team_id),
					   key(type),
					   key(is_working),
					   key(is_ours),
					   key(service_id));

create table script_payload (id int not null auto_increment, primary key(id),
	                         script_id int(11) not null,
							 payload longblob not null,
							 created_on varchar(30) not null,
							 key(script_id),
							 key(created_on));

create table team_scripts_run_status (id int not null auto_increment, primary key(id),
	   		 						  team_id int(11) not null,
									  tick_id int(11) not null,
									  json_list_of_scripts_to_run varchar(10485760) not null,
									  created_on varchar(30) not null,
									  key(tick_id));

create table exploit_attacks (id int not null auto_increment, primary key(id),
	   		 				  script_id int(11) not null,
							  service_id int(11) not null,
							  defending_team_id int(11) not null,
							  attacking_team_id int(11) not null,
							  is_attack_success tinyint(1) not null,
							  created_on varchar(30) not null,
							  key(script_id),
							  key(is_attack_success),
							  key(created_on),
							  key(defending_team_id, service_id, created_on));

create table script_runs (id int not null auto_increment, primary key(id),
	                      script_id int(11) not null,
						  defending_team_id int (11) not null,
						  error int(11) not null,
						  error_msg varchar(2048),
						  created_on varchar(30) not null);	

create table flags (id int not null auto_increment, primary key(id),
	                team_id int(11) not null,
                    service_id int(11) not null,
					flag varchar(128) not null,
					flag_id varchar(128),
					cookie varchar(128),
					created_on varchar(30) not null,
					unique key(flag),
					key(team_id),
					key(service_id),
					key(team_id, service_id),
					key(created_on));

create table flag_submission (id int not null auto_increment, primary key(id),
	   		 	   	          team_id int(11) not null,
							  flag varchar(128) not null,
							  created_on varchar(30) not null,
							  key(team_id),
							  key(flag),
							  unique key(team_id, flag),
							  key(created_on));


create table ticks (id int not null auto_increment, primary key(id),
	                time_to_change varchar(30) not null,
	   		 	    created_on varchar(30) not null,
					key(created_on));

commit;
