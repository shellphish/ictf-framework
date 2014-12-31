require 'httparty'
require './config'

REFRESH_INTERVAL = 1  # seconds

# - DB INTERFACE --------------------------------------------------------------
module Game
  include HTTParty
  format :json
  base_uri CONFIG['api_base_url']
  default_params secret: CONFIG['api_secret']

  def self.ctf_services
    # Retrieve all the flag ids in a team_id => {service_id => flag_id} Hash
    team_flag_ids = get('/getlatestflagids')["flag_ids"]
    # Reorganize so that the Hash is service_id => {team_id => flag_id}
    service_flag_ids = team_flag_ids.each_with_object(Hash.new) do |team_data, h|
      team_id, team_flags = team_data
      (team_flags || {}).each do |service_id, flag_id|
        h[service_id.to_i] ||= []
        h[service_id.to_i] << {team_id: team_id.to_i, flag_id: flag_id}
      end
    end
    # Fetch the services description, merge with the flag ids, and return
    services = get('/getgameinfo')['services']
    Hash[services.map do |s|
     [ s['service_id'],
       { name: s['service_name'],
         port: s['port'],
         description: s['description'],
         flag_id: {
           description: s['flag_id_description'],
           flag_ids: service_flag_ids[s['service_id'].to_i]
         }
       }
     ]
    end]
  end

  def self.ctf_services_status
    get('/getservicesstate')['teams']
  end

  def self.ctf_teams
    @teams ||= Hash[get('/getgameinfo')['teams'].map do |team|
      [team['team_id'].to_i, team]
    end]
  end

  def self.ctf_scores
    Hash[get('/scores')['scores'].map do |team_id, score_hash|
      team = ctf_teams[team_id.to_i]
      next if team.nil?
      [team['team_name'], score_hash]
    end]
  end

end
#-----------------------------------------------------------------------------
while true do
  Game.singleton_methods.select{|m| m.match(/^ctf/)}.each do |m|
    puts "Refreshing #{m}"
    REDIS.set m, Game.send(m).to_json
  end
  sleep(REFRESH_INTERVAL)
end


