start transaction;

drop table if exists teams;
drop table if exists scripts;
drop table if exists team_points;
drop table if exists services;
drop table if exists team_service_state;
drop table if exists netflows;
drop table if exists team_guesses;
drop table if exists exploit_attacks;
drop table if exists flags;
drop table if exists script_runs;
drop table if exists script_payload;
drop table if exists ticks;
drop table if exists game;
drop table if exists team_scripts_run_status;
drop table if exists team_score;
drop table if exists team_credits;
drop table if exists level_score_limit;
drop table if exists levels;
drop table if exists team_level;
drop table if exists level_active_state;
drop table if exists merch;
drop table if exists team_merch_bids;
drop table if exists team_merch_results;
drop table if exists level_nodes;
drop table if exists node_service;
drop table if exists team_services_active_tick;
drop table if exists team_exploited_service;
drop table if exists team_service_tick_status;

create table game (id int);

create table teams (id int not null auto_increment, primary key(id),
	   		 	   	team_name varchar(256) not null, unique key(id),
					team_size int(11),
					team_country varchar(256),
					team_address varchar(256),
					team_logo varchar(2048),
					university_name varchar(256),
					university_url varchar(256),
					ip_range varchar(24) not null,
					created_on varchar(30) not null);
					
create table services (id int not null auto_increment, primary key(id),
	   		 		   name varchar(256) not null, unique key(id),
					   port int not null,
					   description text not null,
					   authors varchar(2048) not null,
					   flag_id_description varchar(2048) not null,					   
					   created_on varchar(30) not null);

/*insert into services (name, port) values ('example', 9999), ('nuclearboom', 4444), ('s1', 1337), ('s2', 4242), ('s3', 4141), ('powerplan', 9898), ('s5', 1212), ('s6', 1234);*/


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

create table levels (id int not null auto_increment, primary key(id),
	   		 		 name varchar(256) not null,
					 created_on varchar(30) not null);

create table level_nodes (id int not null auto_increment, primary key(id),
	   		 		      level_id int(11) not null,
						  name varchar(255) not null,
						  the_order int unsigned not null,
					 	  created_on varchar(30) not null,
						  key(level_id),
						  key(the_order),
						  key(name));

create table node_service (id int not null auto_increment, primary key(id),
	   		 		       node_id int(11) not null,
						   service_id int(11) not null,						   
					 	   created_on varchar(30) not null,
						   key(node_id),
						   key(service_id));
					 
create table level_score_limit (id int not null auto_increment, primary key(id),
						 	    level_id int(11) not null,
						 	   	score_limit int unsigned not null,
						 	   	created_on varchar(30) not null,
								key(level_id),
								key(created_on));

create table team_level (id int not null auto_increment, primary key(id),
	   		 			 team_id int(11) not null,
						 level_id int(11) not null,
						 created_on varchar(30) not null,
						 key(team_id),
						 key(level_id));						 

create table team_score (id int not null auto_increment, primary key(id),
	   		 			 team_id int(11) not null,
						 level_id int(11) not null,
						 score int not null,
						 reason varchar(256) not null,
						 created_on varchar(30) not null,
						 key(team_id),
						 key(level_id),
						 key(team_id, level_id),
						 key(created_on));

create table team_credits (id int not null auto_increment, primary key(id),
	   		 			   team_id int(11) not null,
						   credits int not null,
						   reason varchar(256) not null,
						   created_on varchar(30) not null,
						   key(team_id),
						   key(created_on));

create table merch (id int not null auto_increment, primary key(id),
	   		 	   	name varchar(255) not null,
					description varchar(2048) not null,
					min_bid int unsigned not null,
					num_winners int unsigned not null,
					max_wins int unsigned not null,
					extra_info enum('exploit', 'team'),
					created_on varchar(30) not null);

create table team_merch_bids (id int not null auto_increment, primary key(id),
	   		 	   			  team_id int(11) not null,
							  merch_id int(11) not null,
							  tick_id int(11) not null,
							  is_successful tinyint(1) not null,
							  bid int not null,
							  message varchar(255) not null,
							  extra_info varchar(255),
							  created_on varchar(30) not null,
							  key(team_id),
							  key(is_successful),
							  key(merch_id),
							  key(team_id, is_successful, merch_id));

create table team_merch_results (id int not null auto_increment, primary key(id),
	   		 	   			  	 team_id int(11) not null,
							  	 merch_id int(11) not null,
							  	 tick_id int(11) not null,
								 extra_info int(11) not null,
							  	 the_result int(11) not null,
							  	 created_on varchar(30) not null,
							  	 key(team_id),
							  	 key(tick_id),
								 key(merch_id),
								 key(extra_info, merch_id));


create table netflows (id int not null auto_increment, primary key(id),
	   		 		   team_id int(11) not null,
					   service_id int(11) not null,
					   script_id int(11) not null,
					   session varchar(24) not null,
					   source_ip varchar(24) not null,
					   source_port varchar(24) not null,
					   dest_ip varchar(24) not null,
					   dest_port varchar(24) not null,
					   is_malicious tinyint(1) not null,					   
					   created_timestamp varchar(128) not null,
					   created_on varchar(30) not null,
					   marked_status enum('notmarked', 'correct', 'incorrect') not null,
					   key(created_on),
					   key(team_id),
					   key(session),
					   key(team_id, is_malicious),
					   key(script_id, created_on));

create table team_guesses (id int not null auto_increment, primary key(id),
	   		 			   team_id int(11) not null,
						   netflow_id int(11) not null,
						   session varchar(24) not null,
						   service_id int(11) not null,
						   is_correct tinyint(1) not null,
						   created_on varchar(30) not null,
						   unique key team_netflow (team_id, netflow_id),
						   unique key team_service_session (team_id, service_id, session),
						   key(is_correct),
						   key(team_id, is_correct),
						   key(team_id, service_id, created_on));

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

create table team_services_active_tick (id int not null auto_increment, primary key(id),
	   		 						   	team_id int(11) not null,
										service_id int(11) not null,												
										tick_id int(11) not null,
										created_on varchar(30) not null,
										key (tick_id, team_id));
										


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

create table ticks (id int not null auto_increment, primary key(id),
	                time_to_change varchar(30) not null,
	   		 	    created_on varchar(30) not null,
					is_first_of_round tinyint(1) not null,
					key(is_first_of_round),
					key(created_on),
					key(is_first_of_round, created_on));

create table level_active_state (id int not null auto_increment, primary key(id),
	   	                         level_id int(11) not null,
								 tick_id int(11) not null,
								 active_state varchar(1024) not null,
	   		 	    			 created_on varchar(30) not null,
								 key(level_id),
								 key(tick_id),
								 key(created_on));

create table team_exploited_service (id int not null auto_increment, primary key(id),
	  							    attacking_team_id int(11) not null,
									defending_team_id int(11) not null,
									service_id int(11) not null,
									tick_id int(11) not null,
									was_successful tinyint(1) not null,
									was_detected tinyint(1) not null,
									created_on varchar(30) not null,
									key(service_id),
									key(attacking_team_id, service_id),
									key(defending_team_id, service_id),
									key(service_id, was_successful, was_detected, tick_id),
									key(attacking_team_id, service_id, was_successful, was_detected, tick_id));

create table team_service_tick_status (id int not null auto_increment, primary key(id),
	  							       team_id int(11) not null,
									   service_id int(11) not null,
									   tick_id int(11) not null,
									   is_up tinyint(1) not null,
									   created_on varchar(30) not null,
									   key(service_id));
									   

commit;
