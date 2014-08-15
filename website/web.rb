require 'sinatra'
require 'sinatra/contrib'
require 'yaml'
require 'httparty'
require 'haml'

# - CONFIGURATION -------------------------------------------------------------
configure do
  CONFIG =  YAML.load_file('config.yml')
  set :protection, :except => [:http_origin]
  set :name, CONFIG['name'] || 'CTF'
  set :author, 'Luca Invernizzi <luca@lucainvernizzi.net>'
  set :haml, {format: :html5}
end
# -----------------------------------------------------------------------------


# - AUTHENTICATION ------------------------------------------------------------
helpers do
  def protected!
    return if authorized?
    headers['WWW-Authenticate'] = 'Basic realm="Log in with your team credentials"'
    halt 401, "Not authorized"
  end

  def authorized?
    @auth ||=  Rack::Auth::Basic::Request.new(request.env)
    return false unless @auth.provided? and @auth.basic? and @auth.credentials
    @team_id = CONFIG['teams'].select do |team_id, team_data|
      team_data['name'] == @auth.credentials[0] && team_data['hashed_password'] == @auth.credentials[1]
    end.map{|team_id, team_data| team_id}.first
    !@team_id.nil?
  end
end
# -----------------------------------------------------------------------------


# - DB INTERFACE --------------------------------------------------------------
class Game
  include HTTParty
  format :json
  base_uri CONFIG['api_base_url']
  default_params secret: CONFIG['api_secret']

  def initialize(team_id)
    @team_id = team_id
  end

  def services
    # Retrieve all the flag ids in a team_id => {service_id => flag_id} Hash
    team_flag_ids = self.class.get('/getlatestflagids')["flag_ids"]
    # A team should not know its own flag id
    team_flag_ids.reject!{|team_id| team_id == @team_id.to_s}
    # Reorganize so that the Hash is service_id => {team_id => flag_id}
    service_flag_ids = team_flag_ids.each_with_object(Hash.new) do |team_data, h|
      team_id, team_flags = team_data
      (team_flags || {}).each do |service_id, flag_id|
        h[service_id] ||= []
        h[service_id] << {team_id: team_id, flag_id: flag_id}
      end
    end
    # Fetch the services description, merge with the flag ids, and return  
    services = self.class.get('/getgameinfo')['services']
    Hash[services.map do |s|
     [ s['service_id'],
       { name: s['service_name'],
         port: s['port'],
         description: s['description'],
         flag_id: {
           description: s['flag_id_description'],
           flag_ids: service_flag_ids[s['service_id'].to_s]
         } 
       }
     ]
    end]
  end

  def submit_flag flag
    self.class.get("/submitflag/#{@team_id}/#{flag}")
  end

end

def game
  Game.new(@team_id)
end
#-----------------------------------------------------------------------------


# - WEB INTERFACE ------------------------------------------------------------
respond_to :json
 
get '/', provides: :html do
  respond_with :index
end

get '/services' do
  protected!
  respond_with game.services
end

get '/config' do
  respond_with name: CONFIG['name'] || 'CTF'
end

post '/flag' do
  protected!
  flag = JSON.parse(request.body.read)['flag']
  respond_with game.submit_flag flag if flag
end
#-----------------------------------------------------------------------------
